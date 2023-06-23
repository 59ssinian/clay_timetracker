from tortoise import fields, models


#유저 아이디 비밀번호
class User(models.Model):
    id = fields.IntField(pk=True)
    email = fields.CharField(max_length=255, unique=True)
    password = fields.CharField(max_length=255)
    username = fields.CharField(max_length=255)
    profile_picture = fields.CharField(max_length=255, null=True)
    is_admin = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    social_logins: fields.ReverseRelation['SocialLogin']
    
    def __str__(self):
        return self.email
    
class SocialLogin(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='social_logins')
    provider = fields.CharField(max_length=255)
    provider_id = fields.CharField(max_length=255)
    access_token = fields.CharField(max_length=255)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    def __str__(self):
        return f'{self.provider} - {self.provider_id}'
    
    
#주당근무시간기준입력
class WorkTimeStandard(models.Model):
    id = fields.IntField(pk=True)
    weekworktimestandard = fields.TimeDeltaField()
    recordstart = fields.DateField()
    normaldayworktime = fields.TimeDeltaField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)


#일일 작업 시작 시간, 종료시간, 휴식시간, 총 작업시간, 휴일여부
class DayWorkTime(models.Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="worktime")
    dayworktime_date = fields.DateField()
    dayworktime_start = fields.DatetimeField(null=True)
    dayworktime_end = fields.DatetimeField(null=True)
    dayworktime_rest = fields.TimeDeltaField(null=True)
    dayworktime_total = fields.TimeDeltaField(null=True)
    dayworktime_holiday = fields.BooleanField()
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)

#년도, 월, 기준시작일, 기준 종료일, 주당작업시간, 지정근무시간, 초과여부(True/False)
class WeekWorkTime(models.Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="weekworktime")
    weekworktime_start = fields.DateField()
    weekworktime_end = fields.DateField()
    weekworktime_total = fields.TimeDeltaField()
    weekworktime_over = fields.BooleanField()
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




def __str__(self):
    return f"{self.title}, {self.author_id} on {self.created_at}"