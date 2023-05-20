from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from model import User #User 모델 import

from tortoise import Tortoise

from datetime import date



app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def startup():
    await init_db()

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
        
        #없으면 오늘 날짜에서 시작
        input_date = date.today()
        context = {"request": request, "user": user, "date":input_date}
        return templates.TemplateResponse("index.html", context)
    else:
        return templates.TemplateResponse("login.html", {"request": request})
    






async def init_db():
    await Tortoise.init(
            db_url='postgres://postgres:claytimetracker@localhost:5432/timetracker',
            modules={'models': ['model']},
        )
    await Tortoise.generate_schemas()
