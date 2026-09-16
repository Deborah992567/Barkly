"""Liveness and readiness probes.

`/health` reports process liveness only. `/ready` verifies critical downstream
dependencies (the database, and the configured AI provider's model artifacts
when a provider has a health check) without revealing sensitive diagnostics.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.ai.base import BehaviorInferenceProvider
from app.ai.providers import get_provider
from app.core.config import get_settings
from app.core.request_context import get_request_id
from app.db.session import get_session_factory

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe", include_in_schema=True)
async def health() -> dict:
    return {"status": "ok", "service": "barkly-api", "request_id": get_request_id()}


@router.get("/ready", summary="Readiness probe")
async def ready() -> JSONResponse:
    checks: dict[str, str] = {}
    try:
        async with get_session_factory()() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"

    checks["ai_provider"] = await _ai_provider_check()

    degraded = any(state == "error" for state in checks.values())
    payload = {
        "status": "ready" if not degraded else "unavailable",
        "checks": checks,
    }
    status_code = 200 if not degraded else 503
    return JSONResponse(status_code=status_code, content=payload)


async def _ai_provider_check() -> str:
    try:
        provider: BehaviorInferenceProvider = get_provider(get_settings().ai_provider)
        return "ok" if await provider.health() else "error"
    except Exception:
        return "error"
