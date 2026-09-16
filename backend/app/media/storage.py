"""Storage abstraction for uploaded media.

Phase 2 ships a local-filesystem provider for development. The interface is
deliberately small so a secure object-store provider (S3/GCS) can replace it
without touching services.

Public identifiers are opaque references (UUIDs); filesystem paths and storage
implementation details are never exposed through the API.
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Protocol

from app.core.config import get_settings

_REF_PATTERN = re.compile(r"^[0-9a-f]{32}$")


class StorageProvider(Protocol):
    def save(self, content: bytes, original_name: str | None) -> str: ...

    def delete(self, reference: str) -> None: ...

    def resolve(self, reference: str) -> Path | None:
        """Return a readable local path for a stored reference, or None.

        Used by inference providers to feed stored media into model
        preprocessing without exposing storage internals through the API.
        References that do not match the opaque storage format resolve to None.
        """
        ...


class LocalStorage:
    """Developer storage provider writing files under MEDIA_STORAGE_ROOT."""

    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    def save(self, content: bytes, original_name: str | None = None) -> str:
        reference = uuid.uuid4().hex
        (self._root / reference).write_bytes(content)
        return reference

    def delete(self, reference: str) -> None:
        if not _REF_PATTERN.match(reference):
            return
        path = self._root / reference
        if path.exists():
            path.unlink()

    def resolve(self, reference: str) -> Path | None:
        if not _REF_PATTERN.match(reference):
            return None
        path = self._root / reference
        return path if path.is_file() else None


def get_storage(provider_name: str) -> StorageProvider:
    if provider_name != "local":
        raise ValueError(f"Unsupported media storage provider: {provider_name}")
    settings = get_settings()
    root = Path(settings.media_storage_root).resolve()
    return LocalStorage(root)
