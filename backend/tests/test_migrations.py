"""Migration tests.

Runs the Alembic history against an ephemeral SQLite database by default.
When TEST_DATABASE_URL is exported the same checks run against the real
driver/database there (e.g. MariaDB/MySQL), verifying the production-friendly
migration path.
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
    url = os.environ.get("TEST_DATABASE_URL")
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


def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite")


def _is_mysql(url: str) -> bool:
    return "mysql" in url.split("://", 1)[0]


async def _tables(conn) -> set[str]:
    if _is_sqlite(conn.engine.url.render_as_string()):
        rows = (
            (await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")))
            .scalars()
            .all()
        )
        return set(rows)
    rows = (
        (
            await conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = DATABASE()"
                )
            )
        )
        .scalars()
        .all()
    )
    return set(rows)


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
        table_names = {
            "analyses",
            "analysis_observations",
            "analysis_feedback",
            "media_assets",
        }
        assert table_names.issubset(await _tables(conn))

    await loop.run_in_executor(None, _downgrade)
    async with migration_engine.connect() as conn:
        tables = await _tables(conn)
        # alembic_version may remain; business tables must be gone
        assert not {"users", "dogs", "analyses"}.intersection(tables)
