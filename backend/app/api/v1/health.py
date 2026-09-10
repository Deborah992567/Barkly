"""Liveness and readiness probes.

`/health` reports process liveness only. `/ready` verifies critical downstream
dependencies (the database) without revealing sensitive diagnostics.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.request_context import get_request_id
from app.db.session import get_session_factory

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe", include_in_schema=True)
async def health() -> dict:
    return {"status": "ok", "service": "barkly-api", "request_id": get_request_id()}


@router.get("/ready", summary="Readiness probe")
async def ready() -> JSONResponse:
    check = "ok"
    try:
        async with get_session_factory()() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        check = "error"
    payload = {"status": "ready" if check == "ok" else "unavailable", "checks": {"database": check}}
    status_code = 200 if check == "ok" else 503
    return JSONResponse(status_code=status_code, content=payload)
