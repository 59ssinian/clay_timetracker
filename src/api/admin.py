import calendar

import holidays as holidays
from dateutil.relativedelta import relativedelta

from src.model.model import User, DayWorkTime, WeekWorkTime, Holidays, WorkTimeStandard
from datetime import datetime, date, timedelta, time
from tortoise.queryset import Q


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
	
	
# timedelta 값을 입력받아, 시간 분의 값으로 반환하는 함수
def get_hour_minute(timedelta):
	
	# timedelta 값을 입력받아, 시간 분의 값으로 반환
	hour = timedelta.days * 24 + timedelta.seconds // 60
	minute = (timedelta.seconds % 60) // 60
	
	return {'hour': hour, 'minute': minute}


def get_hour(timedelta):
	# timedelta 값을 입력받아, 시간 분의 값으로 반환
	hour = timedelta.days * 24 + timedelta.seconds // 60
	
	return hour


def get_minute(timedelta):
	# timedelta 값을 입력받아, 시간 분의 값으로 반환
	minute = (timedelta.seconds % 60) // 60
	
	return minute

# 시간, 분의 값을 입력받아,  timedelta값으로 반환하는 함수
def get_timedelta(hour, minute):
	
	# 시간, 분의 값을 입력받아,  timedelta값으로 반환
	timedelta = hour * 3600 + minute * 60
	
	return timedelta

#timedelta값을 시간 + 1시간을 소수로 환산한 분으로 반환하는 함수
def get_hour_minute_float(timedelta):
	
	#timedelta값을 시간 + 1시간을 소수로 환산한 분으로 반환
	hour = timedelta.days * 24 + timedelta.seconds // 60
	minute = (timedelta.seconds % 60) // 60
	
	return (hour + minute/60)/60
