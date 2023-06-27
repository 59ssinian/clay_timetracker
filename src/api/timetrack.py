# BASE import
from fastapi import APIRouter, HTTPException

# DB import
from tortoise.queryset import Q
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel
from src.model.model import User, DayWorkTime, Holidays, LastInputDate, WorkTimeStandard

# Utils
import calendar
import holidays as holidays
from datetime import datetime, date, timedelta, time
import src.api.timeutil as tu


# ROUTER 설정
router = APIRouter()



### 유저 아이디를 받고, 이에 대한 현재 날짜를 기준으로 정보를 반환하는 함수 ###
@router.get("/information/{user_id}")
async def get_information_today(user_id: int):
	#DayWorkTime을 조회하여, 회원 가입일 이후 가장 마지막에 입력된 날짜를 반환
	input_date = await get_input_day(user_id);
	
	# 마지막 입력일이 오늘 날짜를 기준으로 같은주이면, 그 정보를 가져옴
	weekworktime = 0
	isweekworktimeover = False
	
	if tu.is_same_week(input_date, datetime.now().date()):
		weekworktime_list = await  DayWorkTime.filter(user_id=user_id, dayworktime_date__range=[tu.firstday_week(input_date), input_date]).order_by('-dayworktime_date')
		if weekworktime_list:
			weekworktime = tu.timedelta_to_float(weekworktime_list[0].dayworktime_weekworktime)
			isweekworktimeover = weekworktime_list[0].dayworktime_isweekworktimeover
	
	#inputdate를 기준으로 get_input_information을 적용하고, 값을 반환하여, frontend에 반환
	information_today = await get_input_information(user_id, input_date)

	# result 병합
	information_today.update({'weekworktime': weekworktime, 'isweekworktimeover': isweekworktimeover})
	
	return information_today


### 유저 아이디 및 날짜를 받고, 해당 일자를 기준으로 정보를 반환하는 함수 ###
@router.get("/information/{user_id}/{year}/{month}/{day}")
async def get_information_date(user_id: int, year: str, month: str, day: str):
	# yyyy/mm/dd인 date str값을 date 타입으로 변환
	date = year + '/' + month + '/' + day
	input_date = tu.str_to_date(date)
	
	weekworktime = 0
	isweekworktimeover = False
	
	#input_date를 기준으로 시작일, 마지막일의 정보를 반환
	week_first_day = tu.firstday_week(input_date)
	week_last_day = tu.lastday_week(input_date)
	weekworktime_list = await DayWorkTime.filter(user_id=user_id, dayworktime_date__range=[week_first_day,
	                                                                                        week_last_day]).order_by(
		'-dayworktime_date')
	if weekworktime_list:
		weekworktime = tu.timedelta_to_float(weekworktime_list[0].dayworktime_weekworktime)
		isweekworktimeover = weekworktime_list[0].dayworktime_isweekworktimeover

	# inputdate를 기준으로 get_input_information을 적용하고, 값을 반환하여, frontend에 반환
	information = await get_input_information(user_id, input_date)
	
	# result 병합
	information.update({'weekworktime': weekworktime, 'isweekworktimeover': isweekworktimeover})
	
	print('weekworktime', weekworktime)
	
	return information



### 아이디와 입력일을 입력 받아, 해당하는 월의 DayWorkTime의 모든 정보를 반환 ###
async def get_input_information(user_id, input_date):
	
	### 시작일 지정
	# 1) 원칙 : 매날 첫날
	inform_first_day = tu.firstday_month(input_date)
	# 2) 원칙 : 가입일이 첫날 이후라면, 가입일로 수정
		# 가입일 조회
	user_created_at_datetime = await User.filter(id=user_id).values('created_at')
	user_created_at = user_created_at_datetime[0]['created_at'].date()
		# 계산
	if inform_first_day < user_created_at: inform_first_day = user_created_at
	
	### 마지막일 지정
	# 1) 원칙 : 매달 마지막날
	inform_last_day = tu.lastday_month(input_date)
	# 2) 원칙 : 오늘 날짜가 마지막 날짜보다 크면, 오늘 날짜로 수정
	if inform_last_day > datetime.now().date(): inform_last_day = datetime.now().date()
	
	
	
	### 정보 조회
	
	
	# 1) 전체 정보 조회
	# 입력일의 월의 첫번째 날짜와 마지막 날짜 사이의 DayWorkTime 중 입력된 값이 존재하고, dayworktime_isdayoff가 false인 날짜의 정보를 조회
	# dayworktime = await DayWorkTime.filter(user_id=user_id,
	#                                              dayworktime_date__range=[inform_first_day, inform_last_day],
	#                                              dayworktime_isdayoff=False).order_by('dayworktime_date')
	#
	
	# 2) 날짜 및 개별 정보 조회
	# 전체 이벤트 있는 날짜 리스트: - front-end에서 쉽게 보이도록 만들었다.
	inform_days_list = []
	# 전체 이벤트 있는 날짜 리스트: - front-end에서 정보를 쉽게 보이도록 만들었다.
	inform_days_states_list = []
	# 전체 날짜 디테일 리스트: 날짜에 대한 모든 정보를 포함한다.
	dayworktime_detail_list = []
	
	# input_first_day부터 오늘까지, 순차적으로 조회하면서,
	# dayworktime_list에 있는 경우, {date:date, state:'INPUT'}으로,
	# dayoffs_list에 있는 경우, {date:date, state:'DAYOFF'}으로,
	# holidays_list에 있는 경우, {date:date, state:'HOLIDAY'}으로,
	# missing_list에 있는 경우, {date:date, state:'MISSING'}으로,
	# 그 순서는 INPUT과 HOLIDAY가 겹치는 경우 INPUT을 입력하고, HOLIDAY는 무시하도록 하고,
	# INPUT과 DAYOFF가 겹치는 경우 DAYOFF는 무시하고, INPUT을 무시하도록 하고,
	# 이벤트가 있는 날은 input_days_list에 별도로 추가
	
	for i in range((inform_last_day - inform_first_day).days + 1):
		date = inform_first_day + timedelta(days=i)
		
		#해당 날짜의 dayworktime을 검색하여 반환
		date_dayworktime = await DayWorkTime.filter(user_id=user_id,
	                                             dayworktime_date=date).first()
		
		# dayworktime_list에 있는 경우
		if date_dayworktime:
			
			# isdayoff = true인가?
			if date_dayworktime.dayworktime_isdayoff:
		# 1) dayoff인 경우
				inform_days_list.append(tu.date_to_str(date))
				inform_days_states_list.append({'date': tu.date_to_str(date), 'state': 'DAYOFF'})
				dayworktime_detail_list.append({
					'date': date.strftime('%Y/%m/%d'),
					'start_time': '',
					'end_time': '',
					'rest_hour': '',
					'rest_minute': 0,
					'is_dayoff': 0,
					'weekworktime': tu.timedelta_to_float(date_dayworktime.dayworktime_weekworktime)})
				
		# 2) 휴일이 아닌 경우 - 입력상태는 INPUT, 모든 입력값 입력
			else:
				inform_days_list.append(tu.date_to_str(date))
				inform_days_states_list.append({'date': tu.date_to_str(date), 'state': 'INPUT'})
				dayworktime_detail_list.append({
					'date': date.strftime('%Y/%m/%d'),
					'start_time': tu.time_to_str(date_dayworktime.dayworktime_start),
					'end_time': tu.time_to_str(date_dayworktime.dayworktime_end),
					'rest_hour': tu.get_hour(date_dayworktime.dayworktime_rest),
					'rest_minute': tu.get_minute(date_dayworktime.dayworktime_rest),
					'is_dayoff': False,
					'weekworktime': tu.timedelta_to_float(date_dayworktime.dayworktime_weekworktime)})
			
			
		else:
		# 3) holidays에 있는 경우
			inform_days_list.append(tu.date_to_str(date))
			if await Holidays.filter(holiday_date=date, isholiday=True).exists():
				inform_days_states_list.append({'date': tu.date_to_str(date), 'state': 'HOLIDAY'})
			
		# 4) missing에 있는 것으로 취급
			else:
				inform_days_list.append(tu.date_to_str(date))
				inform_days_states_list.append({'date': tu.date_to_str(date), 'state': 'MISSING'})
	
	### console출력
	print("user_id: ", user_id)
	print("input_date: ", input_date)
	print("inform_first_day: ", inform_first_day)
	print("inform_last_day: ", inform_last_day)
	print("input_days_list: ", inform_days_list)
	print("input_days_states_list: ", inform_days_states_list)
	print("dayworktime_detail_list: ", dayworktime_detail_list)
	
	### 반환할 값들을 딕셔너리로 저장
	result = {'input_date': tu.date_to_str(input_date),  # '2021/01/01'
	          'input_days_list': inform_days_list,
	          'input_days_states_list': inform_days_states_list,
	          'dayworktime_detail_list': dayworktime_detail_list}
	
	return result



### 현재 입력해야 하는 날짜 반환 ### for get_information_today
# 가장 마지막으로 입력된 날짜로부터 그다음날부터 휴일을 체크하고, 휴일이 아닌 첫번째 날짜를 반환

async def get_input_day(user_id):
	
	# 1) LastInputDate 에서 마지막 InputDate를 가져옴
	lastinputdate = await LastInputDate.filter(user_id=user_id).order_by('-lastinputdate').first()
	
	# 2) Lastinputedate가 없으면, 회원 가입일자를 가져옴 - 초기 세팅
	if not lastinputdate:
		user_created_at = await User.filter(id=user_id).values('created_at')
		user_created_at_date = user_created_at[0]['created_at'].date()
		count_start_date = user_created_at_date
	else:
	# 3) lastinputdate가 있는 경우, 이것보다 하루 뒤의 값을 시작값으로 지정
		count_start_date = lastinputdate.lastinputdate + timedelta(days=1)
	
	# 4) count_start_date의 다음날짜를 오늘이 될때까지 반복하고, 휴일이 아닌 가장 마지막 날짜를 반환
	today = datetime.today().date()
	
	for i in range((today - count_start_date).days + 1):
		date = count_start_date + timedelta(days=i)
		holiday = await check_holiday(date)
		if holiday:
			print(date," : holiday")
		else:
			print(date, " : no - holiday")
			return date
		
	return today
	


### user_id 및 input_date를 입력 받아,DB에 입력 ### for post_input_dayworktime
# 전달 모델 정의
class InputDayworktime(BaseModel):
	input_date: str
	startTime: str
	endTime: str
	restHour: int
	restMinute: int
	dayoff: bool

@router.post("/post/{user_id}")
async def post_input_dayworktime(user_id: int, input_dayworktime: InputDayworktime):
	
### 1) 사전 준비
	# 해당 데이터를 정리하고, 필요한 값을 계산
	dayworktime_date =  tu.str_to_date(input_dayworktime.input_date)
	
	#user_id값으로 user를 가져옴
	user = await User.filter(id=user_id).first()
	
### 2) 시간 정보 준비
	#dayoff 값이 true인 경우, dayworktime_start=null, dayworktime_end=null, dayworktime_rest=0, dayworktime_total= 0으로 입력
	if input_dayworktime.dayoff:
		dayworktime_start = None
		dayworktime_end = None
		dayworktime_rest = timedelta(hours=0, minutes=0)
		dayworktime_total = timedelta(hours=0, minutes=0)
		dayworktime_isdayoff = True
	else:
		# dayoff 값이 false인 경우, dayworktime_start, dayworktime_end, dayworktime_rest, dayworktime_total 계산
		dayworktime_isdayoff = False
		dayworktime_start = tu.str_to_time(input_dayworktime.startTime)
		dayworktime_end = tu.str_to_time(input_dayworktime.endTime)
		dayworktime_rest = tu.get_timedelta(input_dayworktime.restHour, input_dayworktime.restMinute)
		dayworktime_total = dayworktime_end - dayworktime_start - dayworktime_rest

### 3) 해당 값 입력 및 업데이트

	#dateworktime_date를 기준으로 값이 있으면, update, 없으면, create
	dayworktime = await DayWorkTime.filter(user_id=user_id, dayworktime_date=dayworktime_date).first()
	if dayworktime:
		await DayWorkTime.filter(user_id=user_id, dayworktime_date=dayworktime_date).update(dayworktime_start=dayworktime_start,
		                                                                                   dayworktime_end=dayworktime_end,
		                                                                                   dayworktime_rest=dayworktime_rest,
		                                                                                   dayworktime_total=dayworktime_total,
		                                                                                   dayworktime_isdayoff=dayworktime_isdayoff)
	else:
		await DayWorkTime.create(user=user,
		                         dayworktime_date=dayworktime_date,
		                         dayworktime_start=dayworktime_start,
		                         dayworktime_end=dayworktime_end,
		                         dayworktime_rest=dayworktime_rest,
		                         dayworktime_total=dayworktime_total,
		                         dayworktime_isdayoff=dayworktime_isdayoff)

	
### 4) 주간 근무시간 계산 및 같은 주에 업데이트
	
	# 4-1) dayworktime_weekworktime 계산하고 업데이트도 함.
	weekworktime_result = await get_weekly_worktime(user_id, dayworktime_date)
	
	
	
	
### 5) LastInputDate 업데이트 : 검증된 마지막 날짜를 업데이트, LASTINPUTDATE가 있으면, 그 날짜 이전은 모두 일단 입력 완료다.
	
	# 5-1) DB에서 마지막 LastInputDate를 조회
	last_input_date_db = await LastInputDate.filter(user_id=user_id).order_by('-lastinputdate').first()
	#마지막부터 현재 입력 날짜까지 유효한 값을 조회하고, 도중에 빠진 날이 있으면, 그날을 lastinputdate로 수정
	if last_input_date_db:
		verify_start_date = last_input_date_db.lastinputdate
		for i in range((dayworktime_date - verify_start_date).days):
			date = verify_start_date + timedelta(days=i)
			dayworktime = await DayWorkTime.filter(user_id=user_id, dayworktime_date=date).first()
			if not dayworktime:
				await LastInputDate.filter(user_id=user_id).update(lastinputdate_date=date)
				break
	
	
	#주당 근무시간 값인, weekworktime_result을 반환
	return True
	



'''
***** 휴일 프로세스 *****
'''

# user_id 및 holiday를 입력받으면, dayworktime table에 holiday로 입력하는 함수
async def insert_holiday(user_id, holiday_date):
	dayworktime = DayWorkTime()
	dayworktime.user_id = user_id
	dayworktime.dayworktime_date = holiday_date
	dayworktime.dayworktime_start = datetime.combine(holiday_date, time(0, 0, 0))
	dayworktime.dayworktime_end = datetime.combine(holiday_date, time(0, 0, 0))
	dayworktime.dayworktime_rest = timedelta(hours=0)
	dayworktime.dayworktime_total = timedelta(hours=0)
	dayworktime.dayworktime_holiday = True
	await dayworktime.save()
	
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


'''
***** 근무시간 프로세스 *****
'''
### 새롭게 입력된 주를 기준으로, 해당 주의 주간 근무시간을 계산하는 함수 ###
async def get_weekly_worktime(user_id, dayworktime_date):

# 1) 기준값 세팅
	first_week_day = tu.firstday_week(dayworktime_date)
	last_week_day = tu.lastday_week(dayworktime_date)
	weekworktime = timedelta()
	
# 2) 주간 근무시간 계산 : first_week_day 부터 last_week_day까지의 dayworktime_total을 더함
	for i in range((last_week_day - first_week_day).days + 1):
		date = first_week_day + timedelta(days=i)
		dayworktime = await DayWorkTime.filter(user_id=user_id, dayworktime_date=date).first()
		if dayworktime:
			weekworktime += dayworktime.dayworktime_total
	
# 3) 근무시간 초과여부 계산
# weekworktimestandard를 이용하여 주당 근무시간 기준시간인 weekworktimestandard값을 불러들임
	worktimestandard = await WorkTimeStandard.first()
	standard = worktimestandard.weekworktimestandard
	
	weekworktime_over = False
	
	# 주간 근무시간이 기준시간보다 크면 true 반환
	if weekworktime > standard*60*60: weekworktime_over= True

# 4) weekworktime과 isweekworktimeover를 업데이트
# first_week_day 부터 last_week_day까지 돌면서 입력된 모든 날짜의 dayworktime_weekworktime, dayworktime_isweekworktimeover를 업데이트
	for i in range((last_week_day - first_week_day).days + 1):
		date = first_week_day + timedelta(days=i)
		dayworktime = await DayWorkTime.filter(user_id=user_id, dayworktime_date=date).first()
		if dayworktime:
			await DayWorkTime.filter(user_id=user_id, dayworktime_date=date).update(dayworktime_weekworktime=weekworktime,
			                                                                        dayworktime_isweekworktimeover=weekworktime_over)

	result = {'input_date': dayworktime_date,
	          'dayworktime_weekworktime': weekworktime,
	          'dayworktime_isweekworktimeover': weekworktime_over}

	return result

# user_id, dayworktime_weekworktime, dayworktime_isweekworktimeover를 입력 받아, 해당 주에 DayWorkTime 정보에 대해 dayworktime_weekworktime,dayworktime_isweekworktimeover 를 모두 업데이트 하는 함수
async def update_weekly_worktime(user_id, dayworktime_weekworktime, dayworktime_isweekworktimeover, dayworktime_date):
	# 해당일자가 무슨요일인지 계산
	weekday = dayworktime_date.weekday()

	# 해당일자가 포함된 주의 월요일이 몇일인지 계산
	weekworktime_start = dayworktime_date - timedelta(days=weekday)
	
	# 해당일자가 포함된 주에서 월요일부터 dayworktime_date까지 dayworktime_weekworktime, dayworktime_isweekworktimeover 정보 업데이트
	for n in range(weekday):
		date = weekworktime_start + timedelta(days=n)
		dayworktime = await DayWorkTime.filter(user_id=user_id, dayworktime_date=date).order_by('-id').first()
		if dayworktime:
			dayworktime.dayworktime_weekworktime = dayworktime_weekworktime
			dayworktime.dayworktime_isweekworktimeover = dayworktime_isweekworktimeover
			await dayworktime.save()
		
			
		

	return True



'''
***** admin 프로세스 *****
'''

# 전체 유저 중 오늘 날짜를 기준으로 해당 월에 입력되지 않는 날짜들이 있는 유저들을 조회하는 함수
async def get_unfiled_users():
	
	#오늘 날짜를 기준으로 입력의무가 있는 전일을 조회 : 전일이 일요일인 경우, 금요일로 수정, 전일이 토요일인 경우, 목요일로 수정, 전일이 휴일인 경우 가장 최근 근무일로 수정
	previousday = date.today() - timedelta(days=1)
	while await check_holiday(previousday):
		previousday = previousday - timedelta(days=1)
		
	#전체 user 리스트를 조회하고, 각각의 user에 대해서, dayworktime table 에서 first_day부터 어제까지 입력되지 않는 유저들을 조회
	
	#전체 user 리스트 조회, 단, username=admin인 것은 제외
	user_list = await User.filter(~Q(username='admin'))
	
	#각 user별로 dayworktime table에서 first_day부터 어제까지 입력되지 않는 유저들을 조회
	unfiled_user_list = []
	
	for user in user_list:
		#dayworktime table에서 입력된 마지막 날짜를 조회
		last_day = await DayWorkTime.filter(user=user.id).order_by('-dayworktime_date').first()
		
		#입력된 마지막 날짜가 previousday보다 크면 unfiled_user_list에 추가
		if last_day:
			if previousday > last_day.dayworktime_date:
				unfiled_user_list.append({"displayname": user.displayname, "user_id": user.id, "last_day" : last_day.dayworktime_date})
		else:
			unfiled_user_list.append({"displayname": user.displayname, "user_id": user.id, "last_day" : "날짜없음"})
	
	print(unfiled_user_list)
	return unfiled_user_list

# 년과 월을 입력받고, 해당 월을 기준으로 1일부터 말일까지 휴일정보 및 전체 유저별 해당 날짜 입력 여부를 리스트로 반환하는 함수
async def get_total_user_list(year, month):
	#전체 유저 리스트 조회
	user_list = await User.filter(~Q(username='admin'))
	
	#년, 월에 대한 첫날과 마지막날에 대한 루프
	#해당 월의 첫날과 마지막날을 계산
	first_day = 1
	last_day = calendar.monthrange(year, month)[1]
	
	#사용자 정보 입력하고, 사용자 정보를 리스트로 반환
	total_user_list = []
	#루프 시작
	for user in user_list:
		user_list = []
		#해당 월의 첫날과 마지막날에 대한 루프
		for day in range(first_day, last_day + 1):
			#해당 날짜 입력 여부를 조회
			isinput = await check_user_input(user.id, date(year, month, day))
			user_list.append(isinput)
		
		#사용자 정보를 리스트에 추가
		total_user_list.append({"user_id": user.id, "displayname": user.displayname, "check_list": user_list})
	print(total_user_list)
	return total_user_list

# UTILS : 년월에 대한 휴일정보를 반환
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

	
#유저 정보, 년, 월, 일 정보를 입력받아, 해당 유저의 해당 날짜 입력 여부를 반환하는 함수
async def check_user_input(user_id, day):
	#해당 유저의 해당 날짜 입력 여부를 조회
	dayworktime = await DayWorkTime.filter(user=user_id, dayworktime_date=day).order_by('-id').first()

	# 입력된 날짜가 있으면
	if dayworktime:
		# 해당일이 휴일로 등록되어 있으면,
		if dayworktime.dayworktime_holiday:
			# 휴일로 반환
			return 0
		else:
			# 입력된 날짜가 있으면 시간 반환
			return tu.get_timedelta(dayworktime.dayworktime_total)
	else:
		#입력된 날짜가 없으면 -1 반환
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
		await WorkTimeStandard.create(weekworktimestandard=weekworktimestandard, recordstart=recordstart, normaldayworktime=normaldayworktime)
	
	return True

# WorkTimeStandard에 기준값 조회
async def get_worktimestandard():
	
	# 기준값이 있는지 체크
	worktimestandard_exist = await WorkTimeStandard.first()
	
	return worktimestandard_exist

# user_id, worktimedate를 입력받고 해당 날짜의 정보 반환
async def get_dayworktime(user_id, worktimedate):
	
	# DB에서 user_id, dayworktime_date가 일치하는 데이터를 조회하고. 이중 가장 마지막에 생성된 데이터를 조회
	dayworktime_exist = await DayWorkTime.filter(user_id=user_id, dayworktime_date=worktimedate).order_by('-created_at').first()
	
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
				#토요일 일요일인가?
				elif date(year, month, day).weekday() == 5:
					isholiday = True
				elif date(year, month, day).weekday() == 6:
					isholiday = True
				else:
					isholiday = False
				
				#이미 해당 날짜에 입력된 값이 있는지 체크
				holiday_exist = await Holidays.filter(holiday_date=date(year, month, day)).first()
				
				#입력된 값이 있는 경우 isholiday 값만 업데이트
				if holiday_exist:
					print("이미 입력된 값이 있습니다.")
				#입력된 값이 없는 경우, 해당 날짜를 holiday table에 삽입
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

#해당 년, 월을 입력하면, 해당 년, 월의 휴일을 holidays table에서 조회하여, 리스트로 반환하는 함수
async def get_holidays(year, month):
	
	#해당 년, 월의 휴일을 holidays table에서 조회하여, 리스트로 반환
	holidays_list = await Holidays.filter(holiday_date__year=year, holiday_date__month=month).order_by('holiday_date')
	
	return holidays_list
	

#오늘날짜를 기준으로 다음달 1일의 holiday 정보가 없는 경우, insert_holydays에 다음달 1일의 해를 입력하여 실행
async def init_holiday():
	
	#오늘날짜를 기준으로 다음달 1일의 holiday 정보가 없는 경우, insert_holydays에 다음달 1일의 해를 입력하여 실행
	today = datetime.today().date()
	next_month = today + relativedelta(months=1)
	
	#다음달 1일의 holiday 정보가 없는 경우, insert_holydays에 다음달 1일의 해를 입력하여 실행
	holiday_exist = await Holidays.filter(holiday_date=next_month).first()
	
	if holiday_exist==None:
		print("init holiday : " + str(next_month.year))
		await insert_holidays(next_month.year)
		
	return True



'''
***** admin 프로세스 *****
'''


async def is_recorded(user_id, input_date):

	#해당 날짜에 해당하는 DayWorkTime이 있는지 조회
	dayworktime_exist = await DayWorkTime.filter(user_id=user_id, dayworktime_date=input_date).first()
	
	#해당 날짜에 해당하는 DayWorkTime이 있는 경우 True, 없는 경우 False 반환
	if dayworktime_exist:
		return True
	else:
		return False






















# # 아이디와 입력일을 입력 받아, 해당하는 월의 DayWorkTime의 모든 정보를 반환 oldversion
# async def get_input_information(user_id, input_date):
#
# 	# 입력일의 월의 첫번째 날짜를 구함
# 	input_first_day = input_date.replace(day=1)
#
# 	# 아이디를 기준으로 User DB에 접근하여 해당 아이디의 created_at(datetime값)을 date 타입으로 변환하여 반환
# 	user_created_at_datetime = await User.filter(id=user_id).values('created_at')
# 	user_created_at = user_created_at_datetime[0]['created_at'].date()
#
# 	# 만일 첫번째 날짜가 회원 가입일 이전이라면, 회원 가입일을 input_first_day로 지정
# 	if input_first_day < user_created_at:
# 		input_first_day = user_created_at
#
# 	# input_first_day가 포함된 달의 마지막 날짜를 구함.
# 	input_last_day = input_first_day.replace(day=calendar.monthrange(input_first_day.year, input_first_day.month)[1])
#
# 	# 입력일의 월의 첫번째 날짜와 마지막 날짜 사이의 DayWorkTime 중 입력된 값이 존재하고, dayworktime_isdayoff가 false인 날짜의 정보를 조회
# 	input_dayworktime = await DayWorkTime.filter(user_id=user_id, dayworktime_date__range=[input_first_day, input_last_day], dayworktime_isdayoff=False)
#
# 	# input_dayworktime의 정보 중 입력된 날짜만을 리스트로 반환
# 	dayworktime_list = []
# 	for dayworktime in input_dayworktime:
# 		dayworktime_list.append(dayworktime)
#
#
# 	# 입력일의 월의 첫번째 날짜와 마지막 날짜 사이의 DayWorkTime 중 dayworktime_isdayoff가 true인 날짜를 조회하여, date만의 리스트로 반환
# 	dayworktime_date_dayoffs = await DayWorkTime.filter(user_id=user_id, dayworktime_date__range=[input_first_day, input_last_day], dayworktime_isdayoff=True).values('dayworktime_date')
# 	dayoffs_list = []
# 	for dayoff in dayworktime_date_dayoffs:
# 		dayoffs_list.append(dayoff['dayworktime_date'])
#
#
# 	# 입력일의 월의 첫번째 날짜와 마지막 날짜 사이의 Holidays를 조회하여, isholiday가 true인 date만의 리스트로 반환
# 	holiday_date_holidays = await Holidays.filter(holiday_date__range=[input_first_day, input_last_day], isholiday=True).values('holiday_date')
# 	holidays_list = []
# 	for holiday in holiday_date_holidays:
# 		holidays_list.append(holiday['holiday_date'])
#
#
# 	#input_first_day부터 오늘까지, 순차적으로 조회하면서,
# 	# (1) dayworktime_list에 있는 경우, (2) dayoffs_list에 있는 경우, (3) holidays_list에 있는 경우를 제외한 리스트를 missing list로 반환
# 	missing_list = []
# 	input_today = date.today()
# 	for i in range((input_today - input_first_day).days + 1):
# 		day = input_first_day + timedelta(days=i)
# 		if day not in dayworktime_list and day not in dayoffs_list and day not in holidays_list:
# 			missing_list.append(day)
#
#
# 	# 반환할 값들을 딕셔너리로 저장
# 	result = {'input_date': input_date, # '2021-01-01'
# 		'dayworktime_detail_list': input_dayworktime,
# 	           'input_days_list' : dayworktime_list,
# 	           'dayoffs_list': dayoffs_list,
# 	           'holidays_list': holidays_list,
# 	           'missing_list': missing_list}
#
# 	return result