"""Authentication endpoint tests."""

from __future__ import annotations

import uuid
from datetime import UTC

from httpx import AsyncClient


async def test_register_returns_token_and_user(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"auth-{uuid.uuid4().hex[:8]}@example.com",
            "password": "a-strong-password!",
            "display_name": "Pat",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["expires_in"] > 0
    assert body["user"]["email"].endswith("@example.com")


async def test_register_duplicate_email_conflicts(client: AsyncClient) -> None:
    email = f"dup-{uuid.uuid4().hex[:8]}@example.com"
    payload = {"email": email, "password": "a-strong-password!"}
    assert (await client.post("/api/v1/auth/register", json=payload)).status_code == 201
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EMAIL_TAKEN"


async def test_login_roundtrip(client: AsyncClient) -> None:
    email = f"login-{uuid.uuid4().hex[:8]}@example.com"
    password = "a-strong-password!"
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    assert response.json()["access_token"]


async def test_login_wrong_password_rejected(client: AsyncClient) -> None:
    email = f"bad-{uuid.uuid4().hex[:8]}@example.com"
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "a-strong-password!"}
    )
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "wrong-password!"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


async def test_me_requires_valid_token(client: AsyncClient, user_headers: dict) -> None:
    response = await client.get("/api/v1/auth/me", headers=user_headers)
    assert response.status_code == 200
    assert response.json()["email"].endswith("@example.com")


async def test_expired_token_rejected(client: AsyncClient) -> None:
    from datetime import datetime, timedelta

    import jwt as pyjwt

    from app.core.config import get_settings

    settings = get_settings()
    expired = pyjwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "type": "access",
            "iat": datetime.now(tz=UTC) - timedelta(hours=2),
            "exp": datetime.now(tz=UTC) - timedelta(hours=1),
        },
        settings.effective_jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


async def test_malformed_bearer_rejected(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 401
    assert response.json()["error"]["request_id"]
