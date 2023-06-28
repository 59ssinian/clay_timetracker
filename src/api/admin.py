import calendar
from fastapi import APIRouter, HTTPException, Request, Depends
import holidays as holidays
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel
from src.model.model import User, DayWorkTime, Holidays, WorkTimeStandard
from datetime import datetime, date, timedelta, time
from tortoise.queryset import Q
import src.api.timeutil as tu





router = APIRouter()



'''
***** admin 프로세스 *****
'''

### 전체 STATUS 조회 ###


# start_date에서 end_date 까지 전체 인원의 입력 상황 조회
async def get_admin_status(start_date, end_date):
	
	# 기준일 조회
	worktimestandard = await WorkTimeStandard.first().values('recordstart')
	record_start_day = worktimestandard['recordstart']
	
	# 조회 시간
	total_status_list = []
	total_missing_person = 0
	total_missing_person_list = []
	total_overwork_person_list = []
	total_user = 0
	unfiled_user_list = []
	
	
	# 1) start_date에서 end_date 까지의 휴일 정보를 반환하고, 심플리스트 생성
	holidays_DB = await Holidays.filter(holiday_date__gte=start_date, holiday_date__lte=end_date)\
		.order_by('holiday_date')
	print(start_date, end_date)
	
	holiday_list = []
	for holiday in holidays_DB:
		print(holiday.holiday_date)
		if holiday.isholiday:
			holiday_list.append('H')
		else:
			holiday_list.append('W')
	
	# 2) User 테이블에서 isUser=True인 대상의 리스르를 id 순으로 user 조회
	users = await User.filter(is_user=True).order_by("id")
	total_user = await User.filter(is_user=True).count()
	
	# 3) user_list 에서 user를 얻어, start_date부터 end_date까지 입력 상황을 조회
	# a. user_list에서 user를 얻어옴
	
	for user in users:
		user_id = user.id
		username = user.username
		record_start_date = user.start_date
		create_date = user.created_at.date()
		status_list = []
		overwork_list = []
		missing_days = 0
		isoverwork = False
		
		# b. start_date부터 end_date까지 루프 시작
		for i in range((end_date - start_date).days+1):
			
			date = start_date + timedelta(days=i)
			if date < create_date:
				status_list.append("N")
			else:
		# c. Dayworktime에 userid, dayworktime_date가 존재하는지 확인
				dayworktime = await DayWorkTime.filter(Q(user_id=user.id) & Q(dayworktime_date=date)).first()
				if dayworktime:
					if dayworktime.dayworktime_isdayoff:
						status_list.append("D")
					else:
						status_list.append("I")
						if dayworktime.dayworktime_isweekworktimeover:
							isoverwork = True
				else:
					if (record_start_day <= date and record_start_date <= date) :

						if holiday_list[i] == 'H':
							status_list.append("H")

						else:
							status_list.append("M")
							missing_days += 1
					else:
						status_list.append("N")
		
		if missing_days > 0:
			total_missing_person += 1
			unfiled_user_list.append({'username':username, 'id':user.id, 'missing_days':missing_days})

		if isoverwork:
			total_overwork_person_list.append({'username':username, 'id':user.id})
		
		# d. 전체 정리해서 리스트 생성
		total_status_list.append({
				"user_id":user_id,
				"username": username,
                "status_list": status_list,
                "overwork_list": overwork_list,
                "missing_days": missing_days,
				"isoverwork": isoverwork})
	
	result = {'now': tu.now_str(),
			  'total_user': total_user,
	          'start_date': tu.date_to_str(start_date),
	          'end_date': tu.date_to_str(end_date),
	          'unfiled_user_list': unfiled_user_list,
	          'total_missing_person': total_missing_person,
			  'holiday_list': holiday_list,
	          'total_status_list': total_status_list,
	          'total_overwork_person_list': total_overwork_person_list}
	
	print(result)
	
	return result


# 오늘 입력 상황 조회
@router.get("/status/today")
async def admin_today():
	# 어제 날짜를 구함
	today = date.today()
	
	# 어제 입력 상황을 조회
	status_list = await get_admin_status(today, today)
	
	return status_list

#어제 입력 상황 조회
@router.get("/status/yesterday")
async def admin_yesterday():
	# 어제 날짜를 구함
	yesterday = date.today() - timedelta(days=1)
	
	# 어제 입력 상황을 조회
	status_list = await get_admin_status(yesterday, yesterday)
	
	return status_list

# 지난 주 입력 상황 조회
@router.get("/status/lastweek")
async def admin_lastweek():
	# 지난 주 월요일과 일요일을 구함
	today = date.today()
	last_monday = tu.firstday_week(today - timedelta(days=7))
	last_sunday = tu.lastday_week(today - timedelta(days=7))
	
	# 지난 주 월요일과 일요일 사이의 입력 상황을 조회
	status_list = await get_admin_status(last_monday, last_sunday)
	
	return status_list

# 이번 주 입력 상황 조회
@router.get("/status/currentweek")
async def admin_lastweek():
	# 이번주 월요일과 오늘을 구함
	today = date.today()
	monday = tu.firstday_week(today)
	yesterday = today - timedelta(days=1)
	
	# 지난 주 월요일과 일요일 사이의 입력 상황을 조회
	status_list = await get_admin_status(monday, yesterday)
	
	return status_list


# 지난 달 입력 상황 조회
@router.get("/status/lastmonth")
async def admin_lastmonth():
	# 지난 달 1일과 마지막 날을 구함
	last_firstday = tu.firstday_month(date.today() - relativedelta(months=1))
	last_lastday = tu.lastday_month(date.today() - relativedelta(months=1))
	
	# 지난 달 1일과 마지막 날 사이의 입력 상황을 조회
	status_list = await get_admin_status(last_firstday, last_lastday)
	
	return status_list
	
# 이번 달 입력 상황 조회
@router.get("/status/currentmonth")
async def admin_lastmonth():
	# 이번 달 1일과 오늘을 구함
	today = date.today()
	firstday = tu.firstday_month(today)
	
	# 이번 달 1일과 오늘 사이의 입력 상황을 조회
	status_list = await get_admin_status(firstday, today)
	
	return status_list

class InputYearMonth(BaseModel):
	year : int
	month : int
# 이번 달 입력 상황 조회
@router.post("/status/yearmonth")
async def admin_yearmonth(inputModel : InputYearMonth):
	year = inputModel.year
	month = inputModel.month
	#year과 month의 해당 첫날과 마지막 날을 구함
	firstday = tu.firstday_month(date(year, month, 1))
	lastday = tu.lastday_month(date(year, month, 1))
	
	# 이번 달 1일과 오늘 사이의 입력 상황을 조회
	status_list = await get_admin_status(firstday, lastday)
	
	return status_list

### 유저별 월별 조회


# start_date에서 end_date 까지 전체 인원의 입력 상황 조회
async def get_admin_status_user(user_id, start_date, end_date):
	
	# 1) start_date에서 end_date 까지의 휴일 정보를 반환하고, 심플리스트 생성
	holidays_DB = await Holidays.filter(holiday_date__gte=start_date, holiday_date__lte=end_date) \
		.order_by('holiday_date')
	print(start_date, end_date)
	
	holiday_list = []
	for holiday in holidays_DB:
		print(holiday.holiday_date)
		if holiday.isholiday:
			holiday_list.append('H')
		else:
			holiday_list.append('W')
	
	# 2) User 테이블에서 isUser=True인 대상의 리스르를 id 순으로 user 조회
	user = await User.filter(is_user=True, id=user_id).order_by("id").first()
	
	# 3) user_list 에서 user를 얻어, start_date부터 end_date까지 입력 상황을 조회
	# a. user_list에서 user를 얻어옴
	
	
	username = user.username
	record_start_date = user.start_date
	create_date = user.created_at.date()
	status_list = []
	overwork_list = []
	detail_list = []
	missing_list = []
	inform_days_list = []
	
	# b. start_date부터 end_date까지 루프 시작
	for i in range((end_date - start_date).days + 1):
		date = start_date + timedelta(days=i)
		start_time = ''  # 출근시간
		end_time = ''  # 퇴근시간
		rest_hour = 0   # 휴게시간 시
		rest_minute = 0 # 휴게시간 분
		total_time = 0
		isdayoff = False
		weekworktime = 0
		isoverwork = False
		
		if create_date > date or record_start_date > date :
			status_list.append("N")
		else:
			# c. Dayworktime에 userid, dayworktime_date가 존재하는지 확인
			dayworktime = await DayWorkTime.filter(Q(user_id=user.id) & Q(dayworktime_date=date)).first()

			if dayworktime:
				isdayoff = dayworktime.dayworktime_isdayoff
				if isdayoff:
					status_list.append({'date':tu.date_to_str(date), 'state':"D"})
					inform_days_list.append(tu.date_to_str(date))
				else:
					status_list.append({'date': tu.date_to_str(date), 'state': "I"})
					inform_days_list.append(tu.date_to_str(date))
					start_time = tu.time_to_str(dayworktime.dayworktime_start)
					end_time = tu.time_to_str(dayworktime.dayworktime_end)
					rest_hour = tu.get_hour(dayworktime.dayworktime_rest)
					rest_minute = tu.get_minute(dayworktime.dayworktime_rest)
					total_time = tu.timedelta_to_float(dayworktime.dayworktime_total)
					weekworktime = tu.timedelta_to_float(dayworktime.dayworktime_weekworktime)
					isoverwork = dayworktime.dayworktime_isweekworktimeover
					if isoverwork:
						overwork_list.append(tu.date_to_str(date))
			else:
				if holiday_list[i] == 'H':
					status_list.append({'date': tu.date_to_str(date), 'state': "H"})
					inform_days_list.append(tu.date_to_str(date))
				else:
					status_list.append({'date': tu.date_to_str(date), 'state': "M"})
					inform_days_list.append(tu.date_to_str(date))
					missing_list.append(tu.date_to_str(date))
		
		# d. detail_list에 추가
		detail_list.append({
			"date": tu.date_to_str(date),
			"start_time": start_time,
			"end_time": end_time,
			"rest_hour": rest_hour,
			"rest_minute": rest_minute,
			"total_time": total_time,
			"isdayoff": isdayoff,
			"weekworktime": weekworktime,
			"isoverwork": isoverwork,
		})
	
	# d. 전체 정리해서 리스트 생성
	user_status_list={
		'now': tu.now_str(),
		"username": username,
		"status_list": status_list,
		"overwork_list": overwork_list,
		"detail_list": detail_list,
		"missing_list": missing_list,
		'start_date': tu.date_to_str(start_date),
		'end_date': tu.date_to_str(end_date),
		'holiday_list': holiday_list,
		'inform_days_list':inform_days_list
	}

	
	print(user_status_list)
	
	return user_status_list

# 이번 달 입력 상황 조회

class InputYearMonthUser(BaseModel):
	year: int
	month: int
	user_id: int

@router.post("/status/user/yearmonth")
async def admin_yearmonth(inputModel: InputYearMonthUser):
	year = inputModel.year
	month = inputModel.month
	user_id = inputModel.user_id
	# year과 month의 해당 첫날과 마지막 날을 구함
	firstday = tu.firstday_month(date(year, month, 1))
	lastday = tu.lastday_month(date(year, month, 1))
	today = date.today()
	
	#마지막일이 오늘보다 크면 오늘로 수정
	if lastday > today:
		lastday = today
	
	# 이번 달 1일과 오늘 사이의 입력 상황을 조회
	status_list = await get_admin_status_user(user_id, firstday, lastday)
	
	return status_list



### 권한 설정 페이지 ###


## 전체 유저 리스트 조회 ##
@router.get("/userlist")
async def get_user_list():
	user_list = []
	users = await User.all().order_by('id')
	for user in users:
		id = user.id
		username = user.username
		is_admin = user.is_admin
		is_user = user.is_user
		start_date = user.start_date
		user_list.append({
			"id": id,
			"username": username,
			"is_admin": is_admin,
			"is_user": is_user,
			"start_date": tu.date_to_str(user.start_date),
		})
		
	print(user_list)
	return user_list


@router.get("/userlist/autocomplete")
async def get_user_list_autocomplete():
	username_list = []
	users = await User.all().order_by('id')
	for user in users:
		username = user.username
		username_list.append(username)
	
	print(username_list)
	return username_list


## 유저 권한 수정 ##
class DataRequest_userrole(BaseModel):
	user_id: int
	is_admin: bool
	is_user: bool
	
@router.post("/setting/role")
async def admin_user_role(request: DataRequest_userrole):
	user_id = request.user_id
	is_admin = request.is_admin
	is_user = request.is_user
	user = await User.get(id=user_id)
	user.is_admin = is_admin
	user.is_user = is_user
	await user.save()
	return







### 관리자 설정 페이지 ###









@router.get("/setting/get")
async def admin_get_setting():
	
	worktimestandard = await WorkTimeStandard.get_or_none(id=1)
	
	if worktimestandard:
		context = {
			"weekworktimestandard_hours": tu.timedelta_to_float(worktimestandard.weekworktimestandard),
			"recordstart": worktimestandard.recordstart,
			"normaldayworktime_hours": tu.timedelta_to_float(worktimestandard.normaldayworktime),
		}
	
	return context



class DataRequest_worktimestandard(BaseModel):
	weekworktimestandard_hours: int
	recordstart: date
	normaldayworktime_hours: int


# worktimestandard_input 입력
@router.post("/setting/put")
async def worktimestandard_input(request: DataRequest_worktimestandard):
	print("setting 업데이트")
	# DB에 저장
	# int 값을 시간으로 변환
	weekworktimestandard = tu.hour_to_timedelta(request.weekworktimestandard_hours)
	normaldayworktime = tu.hour_to_timedelta(request.normaldayworktime_hours)
	worktimestandard = await update_worktimestandard(weekworktimestandard, request.recordstart,
	                                                            normaldayworktime)
	print("setting 업데이트완료")
	return worktimestandard


# WorkTimeStandard에 기준값 입력 또는 업데이트
async def update_worktimestandard(weekworktimestandard_hour, recordstart, normaldayworktime_hour):
	# 기준값이 있는지 체크
	worktimestandard_exist = await WorkTimeStandard.first()
	
	if worktimestandard_exist:
		worktimestandard_exist.weekworktimestandard = tu.hour_to_timedelta(weekworktimestandard_hour)
		worktimestandard_exist.recordstart = recordstart
		worktimestandard_exist.normaldayworktime = tu.hour_to_timedelta(normaldayworktime_hour)
		await worktimestandard_exist.save()
	else:
		await WorkTimeStandard.create(weekworktimestandard=tu.hour_to_timedelta(weekworktimestandard_hour), recordstart=recordstart,
		                              normaldayworktime=tu.hour_to_timedelta(normaldayworktime_hour))
	
	return True


# WorkTimeStandard에 기준값 조회
async def get_worktimestandard():
	# 기준값이 있는지 체크
	worktimestandard_exist = await WorkTimeStandard.first()
	
	return worktimestandard_exist


async def is_recorded(user_id, input_date):

	#해당 날짜에 해당하는 DayWorkTime이 있는지 조회
	dayworktime_exist = await DayWorkTime.filter(user_id=user_id, dayworktime_date=input_date).first()
	
	#해당 날짜에 해당하는 DayWorkTime이 있는 경우 True, 없는 경우 False 반환
	if dayworktime_exist:
		return True
	else:
		return False


# 년월에 대한 휴일정보를 반환
async def get_holiday_list(year, month):
	# 년, 월에 대한 첫날과 마지막날에 대한 루프
	# 해당 월의 첫날과 마지막날을 계산
	first_day = 1
	last_day = calendar.monthrange(year, month)[1]
	
	# 휴일 입력하고, 휴일정보를 리스트로 반환
	total_holiday_list = []
	for day in range(first_day, last_day + 1):
		# 해당 날짜에 대한 휴일정보 조회
		ifholiday = await check_holiday(date(year, month, day))
		total_holiday_list.append(ifholiday)
	print(total_holiday_list)
	return total_holiday_list


# 유저 정보, 년, 월, 일 정보를 입력받아, 해당 유저의 해당 날짜 입력 여부를 반환하는 함수
async def check_user_input(user_id, day):
	# 해당 유저의 해당 날짜 입력 여부를 조회
	dayworktime = await DayWorkTime.filter(user=user_id, dayworktime_date=day).order_by('-id').first()
	
	# 입력된 날짜가 있으면
	if dayworktime:
		# 해당일이 휴일로 등록되어 있으면,
		if dayworktime.dayworktime_holiday:
			# 휴일로 반환
			return 0
		else:
			# 입력된 날짜가 있으면 시간 반환
			return tu.timedelta_to_float(dayworktime.dayworktime_total)
	else:
		# 입력된 날짜가 없으면 -1 반환
		return -1


# WorkTimeStandard에 기준값 입력 또는 업데이트
async def update_worktimestandard(weekworktimestandard, recordstart, normaldayworktime):
	# 기준값이 있는지 체크
	worktimestandard_exist = await WorkTimeStandard.first()
	
	if worktimestandard_exist:
		worktimestandard_exist.weekworktimestandard = weekworktimestandard
		worktimestandard_exist.recordstart = recordstart
		worktimestandard_exist.normaldayworktime = normaldayworktime
		await worktimestandard_exist.save()
	else:
		await WorkTimeStandard.create(weekworktimestandard=weekworktimestandard, recordstart=recordstart,
		                              normaldayworktime=normaldayworktime)
	
	return True


# WorkTimeStandard에 기준값 조회
async def get_worktimestandard():
	# 기준값이 있는지 체크
	worktimestandard_exist = await WorkTimeStandard.first()
	
	return worktimestandard_exist


# user_id, worktimedate를 입력받고 해당 날짜의 정보 반환
async def get_dayworktime(user_id, worktimedate):
	# DB에서 user_id, dayworktime_date가 일치하는 데이터를 조회하고. 이중 가장 마지막에 생성된 데이터를 조회
	dayworktime_exist = await DayWorkTime.filter(user_id=user_id, dayworktime_date=worktimedate).order_by(
		'-created_at').first()
	
	return dayworktime_exist


# 해당 년을 입력하면, 해당 년도 휴일을 holidays 모듈에서 kor public holidays를 조회하여 입력하는 함수
async def insert_holidays(year):
	# 해당 년도의 월에 휴일을 holidays 모듈에서 kor public holidays를 조회하여 입력
	kor_holidays = holidays.KR(years=year)
	
	# 해당 년도의 1월 1일부터 12월 31일까지 카운트 하면서, 휴일인 경우 isholiday=true, 휴일이 아닌 경우 isholiday=false로 입력
	for month in range(1, 13):
		for day in range(1, 32):
			
			try:
				
				if date(year, month, day) in kor_holidays:
					isholiday = True
				# 토요일 일요일인가?
				elif date(year, month, day).weekday() == 5:
					isholiday = True
				elif date(year, month, day).weekday() == 6:
					isholiday = True
				else:
					isholiday = False
				
				# 이미 해당 날짜에 입력된 값이 있는지 체크
				holiday_exist = await Holidays.filter(holiday_date=date(year, month, day)).first()
				
				# 입력된 값이 있는 경우 isholiday 값만 업데이트
				if holiday_exist:
					print("이미 입력된 값이 있습니다.")
				# 입력된 값이 없는 경우, 해당 날짜를 holiday table에 삽입
				else:
					await Holidays.create(holiday_date=date(year, month, day), isholiday=isholiday, ifmodified=False)
			
			except:
				print("해당 날짜가 없습니다.")
	
	return True


# 해당 년, 월, 일을 date로 입력하면, 해당 일자를 holiday table에서 수정하는 함수
async def update_holidays(holidays_date, isholiday):
	# 해당 년, 월, 일을 date로 입력하면, 해당 일자의 isholiday를 holiday table에서 수정하고, ismodified=True로 수정
	holiday_exist = await Holidays.filter(holiday_date=holidays_date).first()
	
	if holiday_exist:
		holiday_exist.isholiday = isholiday
		holiday_exist.ifmodified = True
		await holiday_exist.save()
	else:
		await Holidays.create(holiday_date=holidays_date, isholiday=isholiday, ifmodified=True)
	
	return True


# 해당 년, 월을 입력하면, 해당 년, 월의 휴일을 holidays table에서 조회하여, 리스트로 반환하는 함수
async def get_holidays(year, month):
	# 해당 년, 월의 휴일을 holidays table에서 조회하여, 리스트로 반환
	holidays_list = await Holidays.filter(holiday_date__year=year, holiday_date__month=month).order_by('holiday_date')
	
	return holidays_list


# 오늘날짜를 기준으로 다음달 1일의 holiday 정보가 없는 경우, insert_holydays에 다음달 1일의 해를 입력하여 실행
async def init_holiday():
	# 오늘날짜를 기준으로 다음달 1일의 holiday 정보가 없는 경우, insert_holydays에 다음달 1일의 해를 입력하여 실행
	today = datetime.today().date()
	next_month = today + relativedelta(months=1)
	
	# 다음달 1일의 holiday 정보가 없는 경우, insert_holydays에 다음달 1일의 해를 입력하여 실행
	holiday_exist = await Holidays.filter(holiday_date=next_month).first()
	
	if holiday_exist == None:
		print("init holiday : " + str(next_month.year))
		await insert_holidays(next_month.year)
	
	return True


# 날짜가 입력되면, holidate_date가 휴일인지 체크하는 함수
async def check_holiday(dayworktime_date):
	# 해당일자가 휴일인지 체크
	holiday = await Holidays.filter(holiday_date=dayworktime_date).first()
	
	if holiday:
		if holiday.isholiday:
			return True
		else:
			return False
	else:
		return None
	
### 유저 아이디 및 날짜를 받고, 해당 일자를 기준으로 start_date를 수정하는 함수 ###
@router.get("/setting/startdate/{user_id}/{year}/{month}/{day}")
async def put_setting_start_date(user_id: int, year: str, month: str, day: str):
# 유저 아이디 및 날짜를 받고, 해당 일자를 기준으로 start_date를 수정하는 함수
	
	# 해당 유저의 start_date를 조회
	user_exist = await User.filter(id=user_id).first()
	
	if user_exist:
		# 해당 유저의 start_date를 수정
		user_exist.start_date = date(int(year), int(month), int(day))
		await user_exist.save()
	
	return True
	