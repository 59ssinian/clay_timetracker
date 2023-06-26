from datetime import timedelta, datetime


#해당 주의 시작일인 월요일 날짜 반환
def firstday_week(date):
	return date - timedelta(days=date.weekday())

#해당 주의 마지막일인 일요일 날짜 반환
def lastday_week(date):
	return date + timedelta(days=6-date.weekday())

#해당 월의 시작일인 날짜 반환
def firstday_month(date):
	return date.replace(day=1)

#해당 월의 마지막일인 날짜 반환
def lastday_month(date):
	return date.replace(day=1) + timedelta(days=32-date.day)

# 2개의 날짜가 같은 주(월요일부터 일요일 기준)에 속하는가?
def is_same_week(date1, date2):
	if firstday_week(date1) == firstday_week(date2):
		return True
	else:
		return False

# timedelta를 hour의 float으로 변환
def timedelta_to_float(timedelta):
	return (timedelta.days * 24 + timedelta.seconds / 3600)

# date값을 'YY/MM/DD'의 str로 변환
def date_to_str(date):
	return date.strftime('%Y/%m/%d')

# time값을 '00:00'의 str로 변환
def time_to_str(time):
	return time.strftime('%H:%M')

# timedelta 값 중, hour 값을 반환
def get_hour(timedelta):
	return timedelta.days * 24 + timedelta.seconds // 3600

# timedelta 값 중, minute 값을 반환
def get_minute(timedelta):
	return (timedelta.seconds % 3600) // 60

# 'yy/mm/dd' str 값을 datetime이 아닌 date로 변환
def str_to_date(str):
	return datetime.strptime(str, '%Y/%m/%d').date()

# '00:00' str 값을 datetime으로 변환
def str_to_time(str):
	return datetime.strptime(str, '%H:%M')

# int hour, int minute 값을 받아, timedelta로 변환
def get_timedelta(hour, minute):
	return timedelta(hours=hour, minutes=minute)

# 현재 시간을 YYYY년 MM월 DD일 HH시 MM분으로 반환
def now_str():
	return datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')

# hour을 timedelta로 변환
def hour_to_timedelta(hour):
	return timedelta(hours=hour)

# 오늘이 월요일인가?
def is_monday():
	if datetime.today().weekday() == 0:
		return True
	else:
		return False