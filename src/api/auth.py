from fastapi import APIRouter, HTTPException
from tortoise.contrib.pydantic import pydantic_model_creator

from ..model.model import User, SocialLogin


router = APIRouter()

# Pydantic 모델 생성
UserPydantic = pydantic_model_creator(User, name="User")
SocialLoginPydantic = pydantic_model_creator(SocialLogin, name="SocialLogin")


# 회원 가입 처리
@router.post("/register")
async def register(user_data: UserPydantic):
    # 입력 받은 데이터로 User 객체 생성
    user = User(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
    )

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
        return {"user_id": user.id, "username": user.username}
    else:
        # 로그인 실패시 예외 발생
        raise HTTPException(status_code=400, detail="Invalid credentials")


# Google 계정 회원 가입 처리
@router.post("/register/google")
async def register_with_google(user_data: SocialLoginPydantic):
    # Google 계정에서 받은 데이터를 사용하여 User 객체 생성
    user = User(
        username=user_data.username,
        email=user_data.email,
        password=None,
        profile_picture=user_data.profile_picture,
    )

    # User 객체를 저장
    await user.save()

    # Google 계정 로그인 정보 저장
    social_login = SocialLogin(
        user=user,
        provider='google',
        provider_id=user_data.google_id,
        access_token=user_data.access_token,
    )

    # SocialLogin 객체를 저장
    await social_login.save()

    # 회원 가입 성공 메시지 반환
    return {"message": "Registration successful"}


# Google 계정 로그인 처리
@router.post("/login/google")
async def login_with_google(user_data: SocialLoginPydantic):
    # Google 계정 로그인 처리
    # 필요한 로직 작성
    
    # Google 계정에서 제공된 access_token을 사용하여 SocialLogin 객체 조회
    social_login = await SocialLogin.get_or_none(
        provider='google',
        provider_id=user_data.google_id,
        access_token=user_data.access_token,
    )
    
    if social_login:
        # SocialLogin에 연결된 User 객체 반환
        user = social_login.user
        return {"user_id": user.id, "username": user.username}
    else:
        # 로그인 실패시 예외 발생
        raise HTTPException(status_code=400, detail="Invalid Google credentials")

