from fastapi import APIRouter, HTTPException
from tortoise.contrib.pydantic import pydantic_model_creator

from ..model.model import User


router = APIRouter()

# Pydantic 모델 생성
UserPydantic = pydantic_model_creator(User, name="User")


# 회원 가입 처리
@router.post("/register")
async def register(user_data: UserPydantic):
    # 입력 받은 데이터로 User 객체 생성
    user = User(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
    )
    
    # User 객체를 조회하여 첫번째 User인 경우, admin=true로 설정하여 저장
    if await User.all().count() == 0:
        user.is_admin = True
    

    # User 객체를 저장
    await user.save()

    # 회원 가입 성공 메시지 반환
    return {"message": "Registration successful"}


# 로그인 처리
@router.post("/login")
async def login(user_data: UserPydantic):
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
        raise HTTPException(status_code=400, detail="Invalid credentials")


# Google 계정 회원 가입 처리
@router.post("/register/google")
async def register_with_google(user_data: UserPydantic):
    # Google 계정에서 받은 데이터를 사용하여 User 객체 생성
    user = User(
        email=user_data.email,
        password=None,
        username=user_data.username,
        profile_picture=user_data.profile_picture,
        provider='google',
        provider_id=user_data.google_id,
        access_token=user_data.access_token,
    )

    # User 객체를 조회하여 첫번째 User인 경우, admin=true로 설정하여 저장
    if await User.all().count() == 0:
        user.is_admin = True

    # User 객체를 저장 후, # Google 계정에 Foreignkey 적용을 위한 값 반환
    # await user.save()
    await user.save()
    
    # 회원 가입 성공 메시지 반환
    return {"message": "Registration successful"}


# Google 계정 로그인 처리
@router.post("/login/google")
async def login_with_google(user_data: UserPydantic):
    email = user_data.email
    provider = user_data.provider
    privoder_id = user_data.google_id
    # Google 계정 로그인 처리
    # 필요한 로직 작성

    # 이메일을 사용하여 User 객체 조회
    user = await User.get_or_none(email=email)

    if user and user.provider == 'google' and user.provider_id == privoder_id:
        # 로그인 성공시 사용자 정보 반환
        return {"user_id": user.id, "username": user.username,
                "is_admin": user.is_admin, "is_user": user.is_user}
    else:
        # 로그인 실패시 예외 발생
        raise HTTPException(status_code=400, detail="Invalid Google credentials")

