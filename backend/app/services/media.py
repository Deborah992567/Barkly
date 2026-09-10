"""Media service: validate, persist metadata, and store content safely.

The client-facing identity is the media asset id. Storage references are
internal and never returned.
"""

from __future__ import annotations

import uuid
from typing import BinaryIO

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ErrorCode, not_found_error
from app.core.logging import get_logger
from app.db.models import MediaAsset
from app.domain.enums import MediaType
from app.media import validation
from app.media.storage import get_storage
from app.repositories.media import MediaRepository

logger = get_logger(__name__)


class MediaService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._media = MediaRepository(session)

    async def upload(
        self,
        *,
        user_id: uuid.UUID,
        media_type: MediaType,
        filename: str,
        content_type: str,
        stream: BinaryIO,
        duration_ms: int | None = None,
    ) -> MediaAsset:
        validation.validate_content_type(media_type, content_type)
        validation.validate_filename(media_type, filename)

        content = stream.read()
        validation.validate_size(len(content))

        storage = get_storage(_storage_provider_name())
        reference = storage.save(content, filename)

        asset = await self._media.create(
            owner_id=user_id,
            media_type=media_type.value,
            original_filename=filename,
            mime_type=content_type,
            file_size=len(content),
            duration_ms=duration_ms,
            storage_reference=reference,
        )
        await self._session.commit()
        logger.info(
            "media_uploaded",
            extra={"media_id": str(asset.id), "media_type": media_type.value},
        )
        return asset

    async def get_owned_asset(self, user_id: uuid.UUID, media_id: uuid.UUID) -> MediaAsset:
        asset = await self._media.get_by_id_and_owner(media_id, user_id)
        if asset is None:
            raise not_found_error(
                ErrorCode.RESOURCE_NOT_FOUND, "The requested media could not be found."
            )
        return asset


def _storage_provider_name() -> str:
    from app.core.config import get_settings

    return get_settings().media_storage_provider
