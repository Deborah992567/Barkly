"""Registration, login, and current-user endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ErrorCode
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.repositories.users import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserRead

router = APIRouter(tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    summary="Create an account",
)
async def register(
    payload: RegisterRequest, session: AsyncSession = Depends(get_db)
) -> TokenResponse:
    repository = UserRepository(session)
    if await repository.get_by_email(payload.email) is not None:
        raise AppError(
            ErrorCode.EMAIL_TAKEN,
            "An account with this email already exists.",
            status_code=409,
        )
    user = await repository.create(
        email=payload.email,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
    )
    await session.commit()
    token, expires_in = create_access_token(user.id)
    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
        user=UserRead.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in with email and password",
)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_db)) -> TokenResponse:
    repository = UserRepository(session)
    user = await repository.get_by_email(payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise AppError(
            ErrorCode.INVALID_CREDENTIALS,
            "Email or password is incorrect.",
            status_code=401,
        )
    token, expires_in = create_access_token(user.id)
    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
        user=UserRead.model_validate(user),
    )


@router.get("/me", response_model=UserRead, summary="Current authenticated user")
async def me(user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(user)
