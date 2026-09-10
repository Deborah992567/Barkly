"""Authentication dependency: resolves the current user from a bearer token."""

from __future__ import annotations

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import unauthenticated_error
from app.core.security import decode_access_token
from app.db.models import User
from app.db.session import get_db
from app.repositories.users import UserRepository

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthenticated_error()
    try:
        user_id = decode_access_token(credentials.credentials)
    except (jwt.PyJWTError, ValueError) as exc:
        raise unauthenticated_error("Invalid or expired access token.") from exc
    user = await UserRepository(session).get_by_id(user_id)
    if user is None:
        raise unauthenticated_error("The account for this token no longer exists.")
    return user
