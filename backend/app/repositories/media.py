"""Media asset persistence (uploaded but possibly unattached media)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MediaAsset


class MediaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        owner_id: uuid.UUID,
        media_type: str,
        original_filename: str | None,
        mime_type: str,
        file_size: int,
        duration_ms: int | None,
        storage_reference: str,
        metadata: dict[str, Any] | None = None,
    ) -> MediaAsset:
        asset = MediaAsset(
            owner_id=owner_id,
            media_type=media_type,
            original_filename=original_filename,
            mime_type=mime_type,
            file_size=file_size,
            duration_ms=duration_ms,
            media_metadata=metadata,
            storage_reference=storage_reference,
        )
        self._session.add(asset)
        await self._session.flush()
        return asset

    async def get_by_id_and_owner(
        self, media_id: uuid.UUID, owner_id: uuid.UUID
    ) -> MediaAsset | None:
        stmt = select(MediaAsset).where(MediaAsset.id == media_id, MediaAsset.owner_id == owner_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()
