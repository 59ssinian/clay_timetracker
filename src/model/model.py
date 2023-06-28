from tortoise import fields, models


#유저 아이디 비밀번호
class User(models.Model):
    id = fields.IntField(pk=True)
    email = fields.CharField(max_length=255, unique=True)
    password = fields.CharField(max_length=255, null=True)
    username = fields.CharField(max_length=255)
    profile_picture = fields.CharField(max_length=255, null=True)
    is_admin = fields.BooleanField(default=False)
    is_user = fields.BooleanField(default=True)
    provider = fields.CharField(max_length=255, null=True)
    provider_id = fields.CharField(max_length=255, null=True)
    access_token = fields.CharField(max_length=255, null=True)
    start_date = fields.DateField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    

#일일 작업 시작 시간, 종료시간, 휴식시간, 총 작업시간, 휴일여부
class DayWorkTime(models.Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="worktime")
    dayworktime_date = fields.DateField()
    dayworktime_start = fields.DatetimeField(null=True)
    dayworktime_end = fields.DatetimeField(null=True)
    dayworktime_rest = fields.TimeDeltaField(null=True)
    dayworktime_total = fields.TimeDeltaField(null=True)
    dayworktime_isdayoff = fields.BooleanField()
    dayworktime_weekworktime = fields.TimeDeltaField(null=True)
    dayworktime_isweekworktimeover = fields.BooleanField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)

#휴일등록여부
class Holidays(models.Model):
    id = fields.IntField(pk=True)
    holiday_date = fields.DateField()
    holiday_name = fields.CharField(null=True, max_length=30)
    isholiday = fields.BooleanField()
    ifmodified = fields.BooleanField()
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)
    

#마지막 미입력 날짜 정보 저장
class LastInputDate(models.Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="lastinputdate")
    lastinputdate = fields.DateField()
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)

#주당근무시간기준입력
class WorkTimeStandard(models.Model):
    id = fields.IntField(pk=True)
    weekworktimestandard = fields.TimeDeltaField()
    recordstart = fields.DateField()
    normaldayworktime = fields.TimeDeltaField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)







def __str__(self):
    return f"{self.title}, {self.author_id} on {self.created_at}"