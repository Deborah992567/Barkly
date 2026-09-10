"""Media endpoint tests: upload validation, ownership, metadata safe-view."""

from __future__ import annotations

from httpx import AsyncClient

from tests.conftest import assert_error_shape, upload_media


async def test_upload_then_fetch_metadata(client: AsyncClient, user_headers: dict) -> None:
    media_id = await upload_media(client, user_headers)
    response = await client.get(f"/api/v1/media/{media_id}", headers=user_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["media_id"] == media_id
    assert body["media_type"] == "AUDIO"
    assert body["original_filename"] == "bark.mp3"
    assert body["mime_type"] == "audio/mpeg"
    assert body["file_size"] == len(b"fake-audio")
    assert body["duration_ms"] is None


async def test_media_detail_never_leaks_storage_reference(
    client: AsyncClient, user_headers: dict
) -> None:
    media_id = await upload_media(client, user_headers)
    detail = await client.get(f"/api/v1/media/{media_id}", headers=user_headers)
    assert detail.status_code == 200
    body = detail.json()
    assert body["media_id"] == media_id
    assert "storage_ref" not in body
    assert "storage_reference" not in body


async def test_invalid_mime_rejected(client: AsyncClient, user_headers: dict) -> None:
    response = await client.post(
        "/api/v1/media/upload",
        headers=user_headers,
        data={"media_type": "AUDIO"},
        files={"file": ("script.sh", b"#!/bin/sh", "application/x-sh")},
    )
    assert response.status_code == 422
    assert_error_shape(response.json(), "MEDIA_INVALID")


async def test_oversized_upload_rejected(client: AsyncClient, user_headers: dict) -> None:
    big = b"x" * 200_000
    response = await client.post(
        "/api/v1/media/upload",
        headers=user_headers,
        data={"media_type": "AUDIO"},
        files={"file": ("big.mp3", big, "audio/mpeg")},
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "MEDIA_TOO_LARGE"


async def test_foreign_media_invisible(
    client: AsyncClient, user_headers: dict, other_headers: dict
) -> None:
    media_id = await upload_media(client, user_headers)
    response = await client.get(f"/api/v1/media/{media_id}", headers=other_headers)
    assert response.status_code == 404
    assert_error_shape(response.json(), "RESOURCE_NOT_FOUND")


async def test_media_type_mismatch_rejected(client: AsyncClient, user_headers: dict) -> None:
    response = await client.post(
        "/api/v1/media/upload",
        headers=user_headers,
        data={"media_type": "IMAGE"},
        files={"file": ("video.mp4", b"x", "video/mp4")},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "MEDIA_INVALID"
