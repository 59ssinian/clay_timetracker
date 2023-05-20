from tortoise import fields, models

#유저 아이디 비밀번호
class Users(models.Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=30, unique=True)
    displayname = fields.CharField(max_length=30, null=True)
    password = fields.CharField(max_length=128, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)

#일일 작업 시작 시간, 종료시간, 휴식시간, 총 작업시간, 휴일여부
class DayWorkTimes(models.Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.Users", related_name="worktime")
    dayworktime_date = fields.DateField()
    dayworktime_start = fields.DatetimeField()
    dayworktime_end = fields.DatetimeField()
    dayworktime_rest = fields.TimeDeltaField(null=True)
    dayworktime_total = fields.TimeDeltaField(null=True)
    dayworktime_holiday = fields.BooleanField()
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)

#년도, 월, 기준시작일, 기준 종료일, 주당작업시간, 지정근무시간, 초과여부(True/False)
class WeekWorkTimes(models.Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.Users", related_name="weekworktime")
    year = fields.IntField()
    month = fields.IntField()
    weekworktime_start = fields.DateField()
    weekworktime_end = fields.DateField()
    weekworktime = fields.TimeDeltaField()
    weekworktime_designated = fields.TimeDeltaField()
    weekworktime_over = fields.BooleanField()
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)

#휴일등록여부
class Holidays(models.Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.Users", related_name="holiday")
    holiday_date = fields.DateField()
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)





def __str__(self):
    return f"{self.title}, {self.author_id} on {self.created_at}"