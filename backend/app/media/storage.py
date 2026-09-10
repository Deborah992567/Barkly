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


def get_storage(provider_name: str) -> StorageProvider:
    if provider_name != "local":
        raise ValueError(f"Unsupported media storage provider: {provider_name}")
    settings = get_settings()
    root = Path(settings.media_storage_root).resolve()
    return LocalStorage(root)
