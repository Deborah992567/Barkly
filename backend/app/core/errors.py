"""Application error contract.

All domain/business failures surface as `AppError` with a stable machine
`code` and a human `message`. HTTP handlers translate them into the single
error envelope documented in docs/api-contract.md. Internal exception details
are logged, never returned to clients.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    DOG_NOT_FOUND = "DOG_NOT_FOUND"
    ANALYSIS_NOT_FOUND = "ANALYSIS_NOT_FOUND"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    CONFLICT = "CONFLICT"
    EMAIL_TAKEN = "EMAIL_TAKEN"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    MEDIA_INVALID = "MEDIA_INVALID"
    MEDIA_TOO_LARGE = "MEDIA_TOO_LARGE"
    MEDIA_UNSUPPORTED = "MEDIA_UNSUPPORTED"
    ANALYSIS_UNAVAILABLE = "ANALYSIS_UNAVAILABLE"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    INVALID_OPERATION = "INVALID_OPERATION"


class AppError(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        status_code: int,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


def validation_error(message: str, details: list[dict[str, Any]] | None = None) -> AppError:
    return AppError(ErrorCode.VALIDATION_ERROR, message, status_code=422, details=details)


def not_found_error(code: ErrorCode, message: str) -> AppError:
    return AppError(code, message, status_code=404)


def conflict_error(message: str) -> AppError:
    return AppError(ErrorCode.CONFLICT, message, status_code=409)


def forbidden_error(message: str) -> AppError:
    return AppError(ErrorCode.FORBIDDEN, message, status_code=403)


def unauthenticated_error(message: str = "Authentication required.") -> AppError:
    return AppError(ErrorCode.UNAUTHENTICATED, message, status_code=401)
