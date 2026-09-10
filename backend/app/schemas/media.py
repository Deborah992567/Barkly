"""Media metadata schemas.

Internal storage references are never exposed; clients reference media by
opaque `media_id` only.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from app.domain.enums import MediaType
from app.schemas.common import APIModel


class MediaUploadRequest(APIModel):
    media_type: MediaType


class MediaAssetRead(APIModel):
    media_id: UUID
    media_type: MediaType
    original_filename: str | None
    mime_type: str
    file_size: int
    duration_ms: int | None
    media_metadata: dict[str, Any] | None
    created_at: datetime


class MediaUploadResponse(MediaAssetRead):
    pass


class MediaMetadataCreate(APIModel):
    media_id: UUID
    media_type: MediaType
    duration_ms: int | None = Field(default=None, ge=0, le=86_400_000)

    @model_validator(mode="after")
    def _duration_for_type(self) -> MediaMetadataCreate:
        if self.duration_ms is not None and self.media_type not in (
            MediaType.AUDIO,
            MediaType.VIDEO,
        ):
            raise ValueError("duration_ms only applies to audio or video media.")
        return self
