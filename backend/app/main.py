"""FastAPI application factory.

Wires configuration, structured logging, request context middleware, CORS,
versioned routers, and the single API error contract. Business logic lives in
services; routes only validate input, resolve dependencies, and serialize.
"""

from __future__ import annotations

import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.ai.providers import get_provider
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware
from app.core.request_context import get_request_id
from app.schemas.errors import ErrorDetail, ErrorEnvelope

logger = get_logger(__name__)

_HTTP_STATUS_TO_CODE: dict[int, ErrorCode] = {
    404: ErrorCode.NOT_FOUND,
    405: ErrorCode.INVALID_OPERATION,
    409: ErrorCode.CONFLICT,
    413: ErrorCode.MEDIA_TOO_LARGE,
    415: ErrorCode.MEDIA_UNSUPPORTED,
    429: ErrorCode.RATE_LIMITED,
}


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    # Fail fast on an unusable provider configuration at startup.
    get_provider(settings.ai_provider)

    app = FastAPI(
        title="BARKLY API",
        version="0.1.0",
        description=(
            "Behavioral interpretation estimates from audio, video, image, and "
            "contextual signals. Not a veterinary diagnostic system."
        ),
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _register_exception_handlers(app)
    _register_routes(app)
    return app


def _register_routes(app: FastAPI) -> None:
    from app.api.v1.health import router as health_router

    app.include_router(health_router)
    app.include_router(api_router, prefix="/api/v1")


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return _error_response(exc.status_code, exc.code.value, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {"field": ".".join(str(part) for part in err["loc"][1:]), "message": err["msg"]}
            for err in exc.errors()
        ]
        return _error_response(
            422, ErrorCode.VALIDATION_ERROR.value, "Request validation failed.", details
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        code = _HTTP_STATUS_TO_CODE.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
        message = str(exc.detail) if exc.detail else "Request failed."
        return _error_response(exc.status_code, code.value, message)

    @app.exception_handler(Exception)
    async def _unexpected_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = get_request_id()
        logger.error(
            "unhandled_exception",
            exc_info=exc,
            extra={"request_id": request_id, "endpoint": request.url.path},
        )
        return _error_response(
            500,
            ErrorCode.INTERNAL_ERROR.value,
            "An unexpected internal error occurred.",
        )


def _error_response(
    status_code: int,
    code: str,
    message: str,
    details: list | None = None,
) -> JSONResponse:
    envelope = ErrorEnvelope(
        error=ErrorDetail(
            code=code,
            message=message,
            request_id=get_request_id() or str(uuid.uuid4()),
            details=details,
        )
    )
    return JSONResponse(status_code=status_code, content=envelope.model_dump())


app = create_app()
