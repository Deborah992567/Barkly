"""Async engine and session factory.

Production targets MariaDB (aiomysql/PyMySQL). In-memory SQLite is supported
so the full API test suite can run hermetically against the same dependency
graph; the in-memory URL must be combined with a StaticPool so all requests share
one underlying connection.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, StaticPool

from app.core.config import get_settings


def create_engine() -> AsyncEngine:
    settings = get_settings()
    url = settings.database_url
    engine_options: dict = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        if ":memory:" in url:
            engine_options["poolclass"] = StaticPool
            engine_options["connect_args"] = {"check_same_thread": False}
        else:
            engine_options["poolclass"] = NullPool
    else:
        engine_options["pool_size"] = 10
        engine_options["max_overflow"] = 20
        engine_options["pool_timeout"] = 30
    return create_async_engine(url, **engine_options)


_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=create_engine(), expire_on_commit=False, class_=AsyncSession
        )
    return _session_factory


def reset_session_factory() -> None:
    """Discard the cached factory (used when tests point settings elsewhere)."""
    global _session_factory
    _session_factory = None


async def get_db() -> AsyncIterator[AsyncSession]:
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        finally:
            await session.close()
