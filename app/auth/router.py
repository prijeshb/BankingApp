from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import log_action
from app.auth import service
from app.auth.dependencies import get_current_user
from app.auth.schemas import (
    AccessTokenResponse,
    LogoutRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.database import get_db
from app.users.models import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await service.register(db, body.email, body.password, body.full_name)
    await log_action(
        db,
        action="user.registered",
        resource_type="User",
        resource_id=user.id,
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    return RegisterResponse(user_id=user.id, email=user.email)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    access_token, refresh_token, user_id = await service.login(db, body.email, body.password)
    await log_action(
        db,
        action="user.login",
        resource_type="User",
        resource_id=user_id,
        user_id=user_id,
        ip_address=request.client.host if request.client else None,
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    access_token = await service.refresh_access_token(db, body.refresh_token)
    return AccessTokenResponse(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    body: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),  # C-1: named so we can pass user_id
):
    await service.logout(db, body.refresh_token, user_id=current_user.id)
    await log_action(
        db,
        action="user.logout",
        resource_type="User",
        resource_id=current_user.id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
