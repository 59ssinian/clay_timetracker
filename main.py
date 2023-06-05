
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from src.model import User, DayWorkTime, WeekWorkTime, Holidays, WorkTimeStandard
from tortoise import Tortoise

from datetime import datetime, date, time, timedelta
from pydantic import BaseModel
from fastapi.responses import JSONResponse

import src.timemanage as timemanage

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# for front-end
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://3.34.198.181:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await init_db()
    await timemanage.init_holiday()

@app.on_event("shutdown")
async def shutdown():
    await Tortoise.close_connections()



@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    #로그인 화면으로 이동
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def root(request: Request):
    #회원가입 화면으로 이동
    return templates.TemplateResponse("signup.html", {"request": request})


#회원가입 시 입력한 정보를 받아서 DB에 저장
@app.post("/signup_process")
async def signup(request: Request, username: str = Form(),
                 password: str = Form(),
                 displayname: str = Form()):

    #DB에 저장
    user = await User.create(username=username, password=password, displayname=displayname)
    return templates.TemplateResponse("login.html", {"request": request})


#로그인 정보 입력 시에 로그인 확인
@app.post("/login_process")
async def login(request: Request, username: str = Form(),
                    password: str = Form()):
    #DB에서 username, password 확인
    user = await User.filter(username=username, password=password).first()
    if user:
        
        #마지막 기재되지 않는 날짜가 있으면 그 날짜에서 시작
        input_date = await timemanage.get_input_day(user.id)
        
        if input_date == None:
            input_date = await timemanage.get_worktimestandard.recordstart()
            print("start_date : "+str(input_date))
        
        
        #주간 근무시간 계산
        
        weekworktimenow = await timemanage.weekly_worktime_now(user.id, input_date)
        
        # 기존 값 조회
        dayworktime = await timemanage.get_dayworktime(user.id, input_date)
        if dayworktime:
            context = {"request": request, "user": user, "date":input_date, "weekworktimenow":weekworktimenow,
                   "dayworktime_start" : dayworktime.dayworktime_start, "dayworktime_end" : dayworktime.dayworktime_end,
                   "dayworktime_rest" : dayworktime.dayworktime_rest,
                   "isrecorded":True, "message":""}
        else:
            context = {"request": request, "user": user, "date": input_date, "weekworktimenow": weekworktimenow,
                       "dayworktime_start": "09:00",
                       "dayworktime_end": "18:00",
                       "dayworktime_rest": "01:00",
                       "isrecorded": False, "message": ""}
        return templates.TemplateResponse("index.html", context)
    else:
        return templates.TemplateResponse("login.html", {"request": request, "message" : "아이디나 비밀번호가 맞지 않습니다"})


class DataRequest_worktime_input(BaseModel):
    user_id: int
    dayworktime_date: date
    dayworktime_start: time
    dayworktime_end: time
    dayworktime_rest: timedelta
    dayworktime_holiday: bool

# 시간정보를 입력 받고, 주당 근무시한을 계산하여 입력하고, 이를 출력해서 보여줌
@app.post("/dayworktime/input")
async def dayworktime_input(request : DataRequest_worktime_input):
    
    # DB에 저장
    # dayworktime 객체를 생성하고 필드에 값 할당
    dayworktime = DayWorkTime()
    dayworktime.user_id = request.user_id
    dayworktime.dayworktime_date = request.dayworktime_date
    
    #휴일인경우 0,0,0 값 입력
    if request.dayworktime_holiday:
        await timemanage.insert_holiday(user_id=request.user_id, holiday_date=request.dayworktime_date)
        print(request.dayworktime_holiday)
        # 처리 결과 반환
        return {"message": str(dayworktime.dayworktime_date)+" 휴일 저장 되었습니다."}
    
    #휴일이 아닌 경우
    else:
        dayworktime.dayworktime_start = datetime.combine(request.dayworktime_date, request.dayworktime_start)
        dayworktime.dayworktime_end = datetime.combine(request.dayworktime_date, request.dayworktime_end)
        dayworktime.dayworktime_rest = request.dayworktime_rest
        # Calculate the total work time
        total_work_time = dayworktime.dayworktime_end - dayworktime.dayworktime_start - request.dayworktime_rest*60
        dayworktime.dayworktime_total = total_work_time
        dayworktime.dayworktime_holiday = request.dayworktime_holiday
        await dayworktime.save()

        result = await timemanage.update_weekly_worktime(dayworktime.user_id, dayworktime.dayworktime_date)
        
        # 처리 결과 반환
        return {"message": str(dayworktime.dayworktime_date)+" 입력 완료 되었습니다."
                                                             "주간 근무시간 : "+str(result["hours"])+"시간"+str(result["minutes"])+"분"}


async def init_db():
    await Tortoise.init(
            db_url='postgres://postgres:claytimetracker@localhost:5432/timetracker',
            modules={'models': ['src.model']},
            #using 'models' directory
            #models.py is generated by tortoise-orm
        )
    
    await Tortoise.generate_schemas()


#Admin 화면 조회 (1) WorkTimeStandard을 조회해서 넘김 (2) 사용자 중 입력되지 않은 유저들을 리스트로 해서 넘김
@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request):

    unfiled_users = await timemanage.get_unfiled_users()
    worktimestandard = await timemanage.get_worktimestandard()
    
    
    if worktimestandard:
        context = {"request": request, "worktimestandard": {
            "weekworktimestandard_hours": worktimestandard.weekworktimestandard.days*24 + worktimestandard.weekworktimestandard.seconds//3600,
            "recordstart": worktimestandard.recordstart,
            "normaldayworktime_hours": worktimestandard.normaldayworktime.days*24 + worktimestandard.normaldayworktime.seconds//3600,
        }, "unfiled_users": unfiled_users}
    else:
        context = {"request": request,  "worktimestandard": {
            "weekworktimestandard_hours": 40,
            "recordstart": date.today(),
            "normaldayworktime_hours": 8,
        }, "unfiled_users": unfiled_users}

    
    return templates.TemplateResponse("admin.html", context)


class DataRequest_worktimestandard(BaseModel):
    weekworktimestandard_hours : int
    recordstart: date
    normaldayworktime_hours : int

#worktimestandard_input 입력
@app.post("/worktimestandard/input")
async def worktimestandard_input(request: DataRequest_worktimestandard):
    print("업데이트")
    #DB에 저장
    #int 값을 시간으로 변환
    weekworktimestandard = timedelta(hours=request.weekworktimestandard_hours)
    print(weekworktimestandard)
    normaldayworktime = timedelta(hours=request.normaldayworktime_hours)
    
    worktimestandard = await timemanage.update_worktimestandard(weekworktimestandard, request.recordstart, normaldayworktime)
    print("업데이트완료")
    return worktimestandard


class DataRequest_worktime_get(BaseModel):
    user_id: int
    dayworktime_date: date
    

#user_id, worktimedate를 입력받아, 해당 날짜에 데이터가 있는 경우 전달
@app.post("/dayworktime/get")
async def dayworktime_get(request: DataRequest_worktime_get):
    
    # 가장 최근의 입력값을 조회
    dayworktime = await timemanage.get_dayworktime(request.user_id, request.dayworktime_date)
    
    
    print(dayworktime.dayworktime_holiday)
    if dayworktime:
        if dayworktime.dayworktime_holiday:
            return {"dayworktime_start": "00:00",
                    "dayworktime_end": "00:00",
                    "dayworktime_rest": 0,
                    "dayworktime_holiday": True,
                    "message": "휴일입니다.",
                    "isrecorded": True}
        else:
            print(dayworktime.dayworktime_rest.seconds)
            return {"dayworktime_start": dayworktime.dayworktime_start.strftime("%H:%M"),
                "dayworktime_end": dayworktime.dayworktime_end.strftime("%H:%M"),
                "dayworktime_rest": dayworktime.dayworktime_rest.seconds,
                "dayworktime_holiday": dayworktime.dayworktime_holiday,
                "message": "데이터가 있습니다.",
                "isrecorded": True}
            
    else:
        return {"dayworktime_start": "00:00",
                "dayworktime_end": "00:00",
                "dayworktime_rest": 0,
                "dayworktime_holiday": False,
                "message": "데이터가 없습니다.",
                "isrecorded": False}
                
