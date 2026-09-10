"""Upload validation.

The client-provided MIME type and filename are advisory only; both are checked
against the supported media-type table. Requests that fail validation are
rejected before any content is stored or executed.
"""

from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings
from app.core.errors import (
    AppError,
    ErrorCode,
)
from app.domain.enums import MediaType

MIME_TABLE: dict[MediaType, set[str]] = {
    MediaType.AUDIO: {
        "audio/mpeg",
        "audio/mp3",
        "audio/mp4",
        "audio/wav",
        "audio/x-wav",
        "audio/aac",
        "audio/ogg",
        "audio/x-m4a",
    },
    MediaType.VIDEO: {
        "video/mp4",
        "video/quicktime",
        "video/x-m4v",
        "video/webm",
    },
    MediaType.IMAGE: {"image/jpeg", "image/png", "image/heic", "image/heif", "image/webp"},
}

_EXTENSION_TABLE: dict[MediaType, set[str]] = {
    MediaType.AUDIO: {".mp3", ".m4a", ".aac", ".wav", ".ogg", ".mp4"},
    MediaType.VIDEO: {".mp4", ".mov", ".m4v", ".webm"},
    MediaType.IMAGE: {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp"},
}


def _media_error(message: str) -> AppError:
    return AppError(ErrorCode.MEDIA_INVALID, message, status_code=422)


def _too_large_error(message: str) -> AppError:
    return AppError(ErrorCode.MEDIA_TOO_LARGE, message, status_code=413)


def validate_content_type(media_type: MediaType, content_type: str | None) -> None:
    if content_type not in MIME_TABLE[media_type]:
        raise _media_error(
            f"Unsupported content type '{content_type}' for {media_type.value} upload."
        )


def validate_filename(media_type: MediaType, filename: str | None) -> None:
    if not filename:
        return
    extension = Path(filename).suffix.lower()
    if extension not in _EXTENSION_TABLE[media_type]:
        raise _media_error(
            f"Unsupported file extension '{extension}' for {media_type.value} upload."
        )


def validate_size(file_size: int) -> None:
    limit = get_settings().max_upload_size_bytes
    if file_size <= 0:
        raise _media_error("Uploaded file is empty.")
    if file_size > limit:
        raise _too_large_error(f"Uploaded file exceeds the {limit} byte limit.")
