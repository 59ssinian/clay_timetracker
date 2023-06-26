from datetime import datetime
from dateutil.relativedelta import relativedelta

import holidays as holidays
from src.model.model import Holidays
from datetime import datetime, date, timedelta, time

from src.api.admin import get_worktimestandard, update_worktimestandard


	### Init Holiday ###

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


	### Init WorktimeStandard ###
	
## WorktimeStandard의 값을 조회해서 아무 값도 없으면 다음의 값을 기본값으로 반환하고,
#값이 있으면 그냥 넘어감
async def init_worktimestandard():
	# get_worktimestandard 를 이용한 조회
	worktimestandard_exist = await get_worktimestandard()
	
	# 조회된 값이 없는 경우, 기본값으로 입력
	if worktimestandard_exist == None:
		print("init worktimestandard")
		weekworktimestandard = 40
		#date 타입으로 2023-07-01을 recordstart에 입력
		recordstart = date(2023, 7, 1)
		
		normaldayworktime   = 8
		
		await update_worktimestandard(weekworktimestandard, recordstart, normaldayworktime)
		