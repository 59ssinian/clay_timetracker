from fastapi import APIRouter, HTTPException
from tortoise.contrib.pydantic import pydantic_model_creator
from pydantic import BaseModel

from ..model.model import User



router = APIRouter()

# Pydantic 모델 생성
UserPydantic = pydantic_model_creator(User, name="User")

class UserModel(BaseModel):
    email: str
    password: str = None
    username: str
    profile_picture: str = None
    is_admin: bool = False
    is_user: bool = True
    provider: str = None
    provider_id: str = None
    access_token: str = None


### 회원 가입 처리
@router.post("/register")
async def register(user_data: UserModel):
    # 입력 받은 데이터로 User 객체 생성
    user = User(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
    )
    
    # User 객체를 조회하여 첫번째 User인 경우, admin=true로 설정하여 저장
    if await User.all().count() == 0:
        user.is_admin = True
    
    # 동일한 이메일이 있는지 검토
    if await User.filter(email=user_data.email).first():
        raise HTTPException(status_code=400, detail="같은 이메일로 가입된 계정이 있습니다.")

    # User 객체를 저장
    await user.save()

    # 회원 가입 성공 메시지 반환
    return {"message": "Registration successful"}

class UserLoginModel(BaseModel):
    email: str
    password: str

# 로그인 처리
@router.post("/login")
async def login(user_data: UserLoginModel):
    email = user_data.email
    password = user_data.password

    # 이메일을 사용하여 User 객체 조회
    user = await User.get_or_none(email=email)

    if user and user.password == password:
        # 로그인 성공시 사용자 정보 반환
        return {"user_id": user.id, "username": user.username,
                "is_admin": user.is_admin, "is_user": user.is_user}
    else:
        # 로그인 실패시 예외 발생
        raise HTTPException(status_code=400, detail="사용자 정보가 일치하지 않습니다.")



# Google 계정 회원 가입 처리
@router.post("/register/google")
async def register_with_google(user_data: UserModel):
    # Google 계정에서 받은 데이터를 사용하여 User 객체 생성
    user = User(
        email=user_data.email,
        password=None,
        username=user_data.username,
        profile_picture=user_data.profile_picture,
        provider='google',
        provider_id=user_data.provider_id,
        # access_token=user_data.access_token,
    )

    # User 객체를 조회하여 첫번째 User인 경우, admin=true로 설정하여 저장
    if await User.all().count() == 0:
        user.is_admin = True

    # 동일한 이메일이 있는지 검토
    if await User.filter(email=user_data.email).first():
        raise HTTPException(status_code=400, detail="같은 이메일로 가입된 계정이 있습니다.")

    # User 객체를 저장 후, # Google 계정에 Foreignkey 적용을 위한 값 반환
    # await user.save()
    await user.save()
    
    # 회원 가입 성공 메시지 반환
    return {"message": "Registration successful"}

class UserGoogleLoginModel(BaseModel):
    email: str
    provider: str
    provider_id: str

# Google 계정 로그인 처리
@router.post("/login/google")
async def login_with_google(user_data: UserGoogleLoginModel):
    email = user_data.email
    provider = user_data.provider
    privoder_id = user_data.provider_id
    # Google 계정 로그인 처리
    # 필요한 로직 작성

    # 이메일을 사용하여 User 객체 조회
    user = await User.get_or_none(email=email)

    if user and user.provider == provider and user.provider_id == privoder_id:
        # 로그인 성공시 사용자 정보 반환
        return {"user_id": user.id, "username": user.username,
                "is_admin": user.is_admin, "is_user": user.is_user}
    else:
        # 로그인 실패시 예외 발생
        raise HTTPException(status_code=400, detail="사용자 정보가 일치하지 않습니다.")

