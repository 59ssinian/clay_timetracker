from src.model import User, DayWorkTime, WeekWorkTime, Holidays, WorkTimeStandard
from datetime import datetime, date, timedelta
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
	#worktimestandard = await WorkTimeStandard.first().weekworktimestandard
	worktimestandard = timedelta(hours=40)
	
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
	
	result = {'weekworktime_start': weekworktime_start, 'weekworktime_end': weekworktime.weekworktime_end,
	          'weekworktime_total': weekworktime.weekworktime_total, 'weekworktime_over': weekworktime.weekworktime_over, 'hours': hours,
	          'minutes': minutes}
	
	return result

#날짜가 입력되면, holidate_date가 휴일인지 체크하는 함수
async def check_holiday(dayworktime_date):
	
	# DB에 같은날짜에 값이 있는지 체크
	ifholiday = await Holidays.filter(holiday_date=dayworktime_date).first()
	
	if ifholiday:
		# 값이 있으면 true 반환
		return True
	else:
		# 값이 없으면 해당 일이 토요일 또는 일요인지 체크하고, 토요일 또는 일요일이면 HOLIDAYS에 휴일 입력하고, TRUE 반환
		if dayworktime_date.weekday() == 5 or dayworktime_date.weekday() == 6:
			await Holidays.create(holiday_date=dayworktime_date)
			return True
		else:
			# 토요일 또는 일요일이 아니면 FALSE 반환
			return False

#해당일을 휴일로 입력하는 함수
async def insert_holiday(dayworktime_date):
	await Holidays.create(holiday_date=dayworktime_date)
	
	
#유저 아이디를 입력하면, 가장 마지막으로 입력된 날짜로부터 휴일을 제외한 그 다음 날짜를 반환하는 함수
async def get_input_day(user_id):
	
	#
	
	
	# DB에 같은날짜에 값이 있는지 체크
	ifdayworktime = await DayWorkTime.filter(user_id=user_id).order_by('-dayworktime_date').first()
	
	# 값이 있으면, 그 다음날짜부터 휴일인이 여부를 체크하고 휴일인 경우 '휴일로 입력하고', 휴일이 아닌 가장 마지막 날짜를 반환
	if ifdayworktime:
		dayworktime_date = ifdayworktime.dayworktime_date + timedelta(days=1)
		print(dayworktime_date)
		while check_holiday(dayworktime_date):
			insert_holiday(user_id, dayworktime_date)
			dayworktime_date = dayworktime_date + timedelta(days=1)
			
			print(dayworktime_date)
	return dayworktime_date
	
	
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
