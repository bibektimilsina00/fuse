from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.v1.auth.dependencies import get_current_user
from apps.api.app.core.config import settings
from apps.api.app.core.database import get_db
from apps.api.app.middleware.rate_limit import limiter
from apps.api.app.models.user import User
from apps.api.app.schemas.auth import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserLogin,
    UserOut,
    UserRegister,
)
from apps.api.app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserOut)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def register(request: Request, user_in: UserRegister, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.register(user_in)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def login(request: Request, user_login: UserLogin, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    user = await auth_service.authenticate(user_login)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_service.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password")
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def forgot_password(request: Request, body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    await auth_service.forgot_password(body.email)
    return {"message": "If your account exists, a password reset link has been sent."}


@router.post("/reset-password")
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def reset_password(request: Request, body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    await auth_service.reset_password(body.token, body.new_password)
    return {"message": "Password has been successfully reset."}
