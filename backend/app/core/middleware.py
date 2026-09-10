"""Per-request middleware: request ids, correlation ids, and structured logs.

Client-supplied request/correlation ids are validated and propagated when safe;
otherwise ids are generated server-side. Request ids are always returned in the
X-Request-Id response header and included in logs and error envelopes.
"""

from __future__ import annotations

import re
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core import request_context
from app.core.logging import get_logger

logger = get_logger(__name__)

_CORRELATION_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]{1,128}$")


def _safe_id(value: str | None, pattern: re.Pattern[str]) -> str | None:
    if value and pattern.match(value):
        return value
    return None


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        tok = request_context.set_request_id(
            _safe_id(request.headers.get("X-Request-Id"), _REQUEST_ID_PATTERN)
            or request_context.new_request_id()
        )
        request_context.set_correlation_id(
            _safe_id(request.headers.get("X-Correlation-Id"), _CORRELATION_PATTERN)
        )

        started = time.perf_counter()
        logger.info(
            "request_started",
            extra={"endpoint": f"{request.method} {request.url.path}"},
        )
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - started) * 1000, 1)
            logger.error(
                "request_failed_unhandled",
                extra={
                    "endpoint": f"{request.method} {request.url.path}",
                    "duration_ms": duration_ms,
                },
            )
            raise
        duration_ms = round((time.perf_counter() - started) * 1000, 1)
        response.headers["X-Request-Id"] = request_context.get_request_id()
        logger.info(
            "request_completed",
            extra={
                "endpoint": f"{request.method} {request.url.path}",
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        request_context.reset(tok)
        return response
