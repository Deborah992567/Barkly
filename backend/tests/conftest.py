"""Test configuration.

The test suite runs hermetically against an in-memory SQLite database via the
same async engine the application uses, so it never touches a developer's real
database. Export TEST_POSTGRES_URL to also exercise migrations against real
PostgreSQL.
"""

from __future__ import annotations

import os

os.environ.setdefault("BARKLY_ENVIRONMENT", "test")
os.environ.setdefault("BARKLY_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("BARKLY_JWT_SECRET", "testing-secret-" + "x" * 32)
os.environ.setdefault("BARKLY_MEDIA_STORAGE_ROOT", "/tmp/barkly-backend-test-media")
os.environ.setdefault("BARKLY_AI_PROVIDER", "development-placeholder")
os.environ.setdefault("BARKLY_MAX_UPLOAD_SIZE_BYTES", "100000")

import uuid  # noqa: E402

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import get_session_factory  # noqa: E402
from app.main import app  # noqa: E402

BASE_URL = "http://test"


@pytest_asyncio.fixture(autouse=True)
async def _managed_db():
    """Create schema before each test and drop it after (test isolation)."""
    factory = get_session_factory()
    engine = factory.kw["bind"]
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    # Release pooled connections bound to this test's event loop
    # (required when running against a connection-pooling backend like
    # PostgreSQL via asyncpg).
    await engine.dispose()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as c:
        yield c


@pytest_asyncio.fixture
async def user_headers(client: AsyncClient) -> dict:
    email = f"user-{uuid.uuid4().hex[:12]}@example.com"
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "a-strong-password!"},
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def other_headers(client: AsyncClient) -> dict:
    email = f"other-{uuid.uuid4().hex[:12]}@example.com"
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "a-strong-password!"},
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def create_dog(client: AsyncClient, headers: dict, name: str = "Max") -> str:
    response = await client.post(
        "/api/v1/dogs",
        headers=headers,
        json={"name": name, "breed": "Beagle", "sex": "MALE"},
    )
    assert response.status_code == 201
    return response.json()["id"]


async def upload_media(
    client: AsyncClient,
    headers: dict,
    media_type: str = "AUDIO",
    filename: str = "bark.mp3",
    content_type: str = "audio/mpeg",
    content: bytes = b"fake-audio",
) -> str:
    response = await client.post(
        "/api/v1/media/upload",
        headers=headers,
        data={"media_type": media_type},
        files={"file": (filename, content, content_type)},
    )
    assert response.status_code == 201, response.text
    return response.json()["media_id"]


def assert_error_shape(payload: dict, code: str, status_has_rid: bool = True) -> None:
    error = payload["error"]
    assert error["code"] == code
    assert error["message"]
    if status_has_rid:
        assert error["request_id"]
