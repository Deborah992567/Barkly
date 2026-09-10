"""Media upload endpoint.

Uploads are validated (MIME, extension, size) and stored via the storage
abstraction; only an opaque `media_id` is returned. Internal storage references
are never exposed.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.domain.enums import MediaType
from app.schemas.media import MediaUploadResponse
from app.services.media import MediaService

router = APIRouter(tags=["media"])


@router.post(
    "/upload",
    response_model=MediaUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a media file for a future analysis",
)
async def upload_media(
    media_type: MediaType = Form(...),
    file: UploadFile = File(...),
    duration_ms: int | None = Form(default=None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MediaUploadResponse:
    asset = await MediaService(session).upload(
        user_id=user.id,
        media_type=media_type,
        filename=file.filename or "upload",
        content_type=file.content_type or "",
        stream=file.file,
        duration_ms=duration_ms,
    )
    return MediaUploadResponse(
        media_id=asset.id,
        media_type=MediaType(asset.media_type),
        original_filename=asset.original_filename,
        mime_type=asset.mime_type,
        file_size=asset.file_size,
        duration_ms=asset.duration_ms,
        media_metadata=asset.media_metadata,
        created_at=asset.created_at,
    )


@router.get(
    "/{media_id}",
    response_model=MediaUploadResponse,
    summary="Get metadata for an owned media asset",
)
async def get_media(
    media_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MediaUploadResponse:
    asset = await MediaService(session).get_owned_asset(user.id, media_id)
    return MediaUploadResponse(
        media_id=asset.id,
        media_type=MediaType(asset.media_type),
        original_filename=asset.original_filename,
        mime_type=asset.mime_type,
        file_size=asset.file_size,
        duration_ms=asset.duration_ms,
        media_metadata=asset.media_metadata,
        created_at=asset.created_at,
    )
