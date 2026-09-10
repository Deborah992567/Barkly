"""Migration tests.

Runs the Alembic history against an ephemeral SQLite database by default.
When TEST_POSTGRES_URL is exported the same checks run against real
PostgreSQL, verifying the production-friendly migration path.
"""

from __future__ import annotations

import asyncio
import os

import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


@pytest_asyncio.fixture
async def migration_engine():
    url = os.environ.get("TEST_POSTGRES_URL")
    if url:
        engine = create_async_engine(url)
        yield engine
        await engine.dispose()
        return

    import tempfile

    handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = handle.name
    handle.close()
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    yield engine
    await engine.dispose()
    os.unlink(db_path)


def _alembic_config(url: str) -> Config:
    here = os.path.dirname(os.path.abspath(__file__))
    ini_path = os.path.join(here, "..", "alembic.ini")
    cfg = Config(ini_path)
    cfg.set_main_option("script_location", os.path.join(here, "..", "migrations"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


async def test_migrations_roundtrip(migration_engine, monkeypatch) -> None:
    url = migration_engine.url.render_as_string(hide_password=False)
    config = _alembic_config(url)
    # migrations/env.py resolves the URL from the environment first.
    monkeypatch.setenv("BARKLY_DATABASE_URL", url)

    loop = asyncio.get_running_loop()

    def _upgrade() -> None:
        command.upgrade(config, "head")

    def _downgrade() -> None:
        command.downgrade(config, "base")

    await loop.run_in_executor(None, _upgrade)
    async with migration_engine.connect() as conn:
        rows = (
            (await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")))
            .scalars()
            .all()
            if url.startswith("sqlite")
            else (
                await conn.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
                )
            )
            .scalars()
            .all()
        )
        table_names = {"analyses", "analysis_observations", "analysis_feedback", "media_assets"}
        if url.startswith("sqlite"):
            assert table_names.issubset(set(rows))
        else:
            assert table_names.issubset(set(rows))

    await loop.run_in_executor(None, _downgrade)
    async with migration_engine.connect() as conn:
        if url.startswith("sqlite"):
            rows = (
                (
                    await conn.execute(
                        text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                    )
                )
                .scalars()
                .all()
            )
            assert rows == []
        else:
            # alembic_version may remain; business tables must be gone
            rows = (
                (
                    await conn.execute(
                        text(
                            "SELECT tablename FROM pg_tables "
                            "WHERE schemaname='public' AND tablename IN ('users','dogs','analyses')"
                        )
                    )
                )
                .scalars()
                .all()
            )
            assert rows == []
