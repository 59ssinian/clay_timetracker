import holidays as holidays
from dateutil.relativedelta import relativedelta

from src.model import User, DayWorkTime, WeekWorkTime, Holidays, WorkTimeStandard
from datetime import datetime, date, timedelta, time
from tortoise.queryset import Q




#새롭게 입력된 주를 기준으로, 해당 주의 주간 근무시간을 계산하는 함수
async def update_weekly_worktime(user_id, dayworktime_date):
	
	# 해당일자가 무슨요일인지 계산
	weekday = dayworktime_date.weekday()
	
	# 해당일자가 포함된 주의 월요일이 몇일인지 계산
	weekworktime_start = dayworktime_date - timedelta(days=weekday)
	# 해당일자가 포함된 주의 일요일이 몇일인지 계산
	weekworktime_end = dayworktime_date + timedelta(days=6-weekday)
	
	# 해당일자가 포함된 주의 월요일부터 일요일까지 근무시간의 합을 계산
	
	worktime = timedelta()
	
	for n in range(7):
		date = weekworktime_start + timedelta(days=n)
		dayworktime = await DayWorkTime.filter(user_id=user_id, dayworktime_date=date).order_by('-id').first()
  
		if dayworktime:
			worktime += dayworktime.dayworktime_total
	
	# weekworktimestandard를 이용하여 주당 근무시간 기준시간인 weekworktimestandard값을 불러들임
	worktimestandard = await WorkTimeStandard.first().weekworktimestandard
	
	# 주간 근무시간이 기준시간보다 작으면 true 크면 false 반환
	if worktime < worktimestandard:
		weekworktime_isstandard = True
	else:
		weekworktime_isstandard = False
	
	weekworktime_over = weekworktime_isstandard
	
	# 해당일자가 포함된 주의 근무시간의 합을 업데이트
	weekworktime = WeekWorkTime()
	weekworktime.user_id = user_id
	weekworktime.weekworktime_start = weekworktime_start
	weekworktime.weekworktime_end = weekworktime_end
	weekworktime.weekworktime_total = worktime
	weekworktime.weekworktime_isstandard = weekworktime_isstandard
	weekworktime.weekworktime_over = weekworktime_over
	
	#DB에 저장
	#해당 주의 시작일을 기준으로 주간 근무시간이 이미 DB에 저장되어있으면, 해당 주의 주간 근무시간을 업데이트
	weekworktime_exist = await WeekWorkTime.filter(user_id=user_id, weekworktime_start=weekworktime_start).first()
	
	if weekworktime_exist:
		weekworktime_exist.weekworktime_total = worktime
		weekworktime_exist.weekworktime_isstandard = weekworktime_isstandard
		weekworktime_exist.weekworktime_over = weekworktime_over
		await weekworktime_exist.save()
	else:
		await weekworktime.save()
	
	#주간 근무시간을 반환
	total_seconds = weekworktime.weekworktime_total.total_seconds()
	
	hours = int(total_seconds // 3600)
	minutes = int((total_seconds % 3600) // 60)
	
	result = {'weekworktime_start': weekworktime_start, 'weekworktime_end': weekworktime_end,
	          'weekworktime_total': worktime, 'weekworktime_over': weekworktime_over, 'hours': hours, 'minutes': minutes}
	
	return result


#아이디와 날짜를 입력받고, 해당 하는 주의 현재 근무시간을 계산하는 함수
async def weekly_worktime_now(user_id, dayworktime_date):
	
	# 해당일자가 무슨요일인지 계산
	weekday = dayworktime_date.weekday()
	
	# 해당일자가 포함된 주의 월요일이 몇일인지 계산
	weekworktime_start = dayworktime_date - timedelta(days=weekday)
	
	# 해당일자가 포함된 주의 워크타임을 조회
	weekworktime = await WeekWorkTime.filter(user=user_id, weekworktime_start=weekworktime_start).first()
	
	if weekworktime:
		# 주간 근무시간을 반환
		total_seconds = weekworktime.weekworktime_total.total_seconds()
	else:
		# 주간 근무시간이 없으면 0을 반환
		total_seconds = 0
	
	hours = int(total_seconds // 3600)
	minutes = int((total_seconds % 3600) // 60)
	
	result = {'hours': hours, 'minutes': minutes}
	
	return result

#날짜가 입력되면, holidate_date가 휴일인지 체크하는 함수
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
	
	

	
	
	
	
	
#유저 아이디를 입력하면, 가장 마지막으로 입력된 날짜로부터 휴일을 제외한 그 다음 날짜를 반환하는 함수
async def get_input_day(user_id):
	print("get_input_day 함수 실행")
	# DB에 같은날짜에 값이 있는지 체크
	ifdayworktime = await DayWorkTime.filter(user_id=user_id).order_by('-id').order_by('-dayworktime_date').first()
	# 오늘날짜를 구함
	today = datetime.today().date()
	# 값이 있으면, 그 다음날짜를 오늘이 될때까지 반복하고, 해당 날짜가 휴일인 경우 '휴일로 입력하고', 휴일이 아닌 가장 마지막 날짜를 반환
	if ifdayworktime:
		workdate = ifdayworktime.dayworktime_date + timedelta(days=1)
		print("값이있음")
		print(workdate, today)
		while workdate <= today:
			holiday = await check_holiday(workdate)
			if holiday:
				# 휴일이면, 휴일로 입력하고, 다음날짜로 넘어감
				await insert_holiday(user_id, workdate)
			print(workdate.strftime('%Y-%m-%d'))
			workdate = workdate + timedelta(days=1)
	else:
		# 값이 없으면, 오늘날짜를 반환
		print("값이없음")
		workdate = today
	
	if (workdate > today):
		workdate = today
	
	# 오늘날짜가 되면, 오늘날짜를 반환
	return workdate
			
		
# user_id 및 holiday를 입력받으면, dayworktime table에 holiday로 입력하는 함수
async def insert_holiday(user_id, holiday_date):
	dayworktime = DayWorkTime()
	dayworktime.dayworktime_start = datetime.combine(holiday_date, time(0, 0, 0))
	dayworktime.dayworktime_end = datetime.combine(holiday_date, time(0, 0, 0))
	dayworktime.dayworktime_rest = timedelta(hours=0)
	dayworktime.dayworktime_total = timedelta(hours=0)
	dayworktime.dayworktime_holiday = True
	await dayworktime.save()
	
	return True
	
	
def get_previous_sunday(date):
    weekday = date.weekday()
    days_to_subtract = (weekday + 1) % 7
    previous_sunday = date - datetime.timedelta(days=days_to_subtract)
    return previous_sunday

def get_current_saturday(date):
    weekday = date.weekday()
    days_to_add = (5 - weekday) % 7
    current_saturday = date + datetime.timedelta(days=days_to_add)
    return current_saturday


# 전체 유저 중 오늘 날짜를 기준으로 해당 월에 입력되지 않는 날짜들이 있는 유저들을 조회하는 함수
async def get_unfiled_users():
	
	#오늘 날짜를 기준으로 입력의무가 있는 전일을 조회 : 전일이 일요일인 경우, 금요일로 수정, 전일이 토요일인 경우, 목요일로 수정, 전일이 휴일인 경우 가장 최근 근무일로 수정
	previousday = date.today() - timedelta(days=1)
	while await check_holiday(previousday):
		previousday = previousday - timedelta(days=1)
		
	#전체 user 리스트를 조회하고, 각각의 user에 대해서, dayworktime table 에서 first_day부터 어제까지 입력되지 않는 유저들을 조회
	#전체 user 리스트 조회
	user_list = await User.all()
	#각 user별로 dayworktime table에서 first_day부터 어제까지 입력되지 않는 유저들을 조회
	unfiled_user_list = []
	
	for user in user_list:
		#dayworktime table에서 입력된 마지막 날짜를 조회
		last_day = await DayWorkTime.filter(user=user.id).order_by('-dayworktime_date').first()
		
		#입력된 마지막 날짜가 previousday가 아니면 unfiled_user_list에 추가
		if last_day:
			if previousday != last_day.dayworktime_date:
				unfiled_user_list.append({"displayname": user.displayname, "user_id": user.id, "last_day" : last_day.dayworktime_date})
		else:
			unfiled_user_list.append({"displayname": user.displayname, "user_id": user.id, "last_day" : "날짜없음"})
	
	print(unfiled_user_list)
	return unfiled_user_list



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


async def is_recorded(user_id, input_date):

	#해당 날짜에 해당하는 DayWorkTime이 있는지 조회
	dayworktime_exist = await DayWorkTime.filter(user_id=user_id, dayworktime_date=input_date).first()
	
	#해당 날짜에 해당하는 DayWorkTime이 있는 경우 True, 없는 경우 False 반환
	if dayworktime_exist:
		return True
	else:
		return False