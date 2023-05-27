from model import User, DayWorkTime


#해당 유저에 대해 날짜에 정보를 입력하는 함수
def insert_time(user, dayWorkTime):
	
	# DB에 같은날짜에 값이 있는지 체크
	ifdayworktime = await DayWorkTime.filter(user_id=user.id, dayworktime_date=dayWorkTime.date).first()
	
	if ifdayworktime:
		# 값이 있으면 업데이트
		result = await DayWorkTime.filter(user_id=user.id, dayworktime_date=dayWorkTime.date).update(dayWorkTime)
	else:
		# 값이 없으면 생성
		result = await DayWorkTime.create(dayWorkTime)
	
	return result


#새롭게 입력된 주를 기준으로, 해당 주의 월요일을 기준으로 시작하여 주간 근무시간을 계산하는 함수
def update_weekly_worktime(user, dayworktime_date):
	
	# 해당 주의 월요일을 기준으로 시작하여 주간 근무시간을 계산
	
	
	# 해당 주의 월요일을 기준으로 시작하여 주간 근무시간을 업데이트
	
	# 해당 주의 월요일을 기준으로 시작하여 주간 근무시간을 출력
	
	pass
	



#해당 유저에 대해 주간 근무시간을 조회하는 함수

#해당 유저에 대해 주간 근무시간을 업데이트하는 함수

#해당 유저에 대해 주간 근무시간을 출력하는 함수

#해당 유저에 대해 주간 근무시간을 삭제하는 함수

#해당 유저에 대해 주간 근무시간을 조회하는 함수


#해당 유저의 입력이 오늘 날짜를 기준으로 빠진 곳이 있는지 체크






#해당 유저에 대해 해당 날짜에 이미 입력된 정보가 있는지 조회하는 함수



#해당 날짜의 시간을 조회하는 함수

#가장 최근에 입력된 값 중에서 휴일이 아닌 날짜를 조회하는 함수

#입력되지 않는 날짜들을 조회하는 함수
