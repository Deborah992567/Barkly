"""History endpoint tests: pagination, filters, ordering."""

from __future__ import annotations

import uuid

from httpx import AsyncClient

from tests.conftest import create_dog, upload_media


async def _seed_analyses(
    client: AsyncClient, headers: dict, count: int, key_prefix: str
) -> list[str]:
    dog_id = await create_dog(client, headers)
    ids: list[str] = []
    for i in range(count):
        response = await client.post(
            "/api/v1/analyses",
            headers=headers,
            json={
                "dog_id": dog_id,
                "input_type": "BEHAVIOR",
                "media_ids": [],
                "idempotency_key": f"{key_prefix}-{i}",
            },
        )
        assert response.status_code == 201, response.text
        ids.append(response.json()["analysis_id"])
    return ids


async def test_history_is_newest_first(client: AsyncClient, user_headers: dict) -> None:
    ids = await _seed_analyses(client, user_headers, 3, f"hist-{uuid.uuid4().hex[:8]}")
    response = await client.get("/api/v1/history", headers=user_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["has_next"] is False
    assert [item["analysis_id"] for item in body["items"]] == list(reversed(ids))


async def test_history_pagination(client: AsyncClient, user_headers: dict) -> None:
    await _seed_analyses(client, user_headers, 5, f"pg-{uuid.uuid4().hex[:8]}")
    page1 = await client.get("/api/v1/history?page=1&page_size=2", headers=user_headers)
    assert page1.status_code == 200
    assert len(page1.json()["items"]) == 2
    assert page1.json()["total"] == 5
    assert page1.json()["has_next"] is True

    page3 = await client.get("/api/v1/history?page=3&page_size=2", headers=user_headers)
    assert len(page3.json()["items"]) == 1
    assert page3.json()["has_next"] is False


async def test_page_size_is_bounded(client: AsyncClient, user_headers: dict) -> None:
    await _seed_analyses(client, user_headers, 3, f"bound-{uuid.uuid4().hex[:8]}")
    response = await client.get("/api/v1/history?page_size=100000", headers=user_headers)
    assert response.status_code == 200
    assert response.json()["page_size"] <= 100


async def test_history_filter_by_dog(client: AsyncClient, user_headers: dict) -> None:
    dog_a = await create_dog(client, user_headers, name="Alpha")
    dog_b = await create_dog(client, user_headers, name="Beta")
    for dog, label in ((dog_a, "a"), (dog_b, "b")):
        await client.post(
            "/api/v1/analyses",
            headers=user_headers,
            json={
                "dog_id": dog,
                "input_type": "BEHAVIOR",
                "media_ids": [],
                "idempotency_key": f"filter-{label}-{uuid.uuid4().hex[:6]}",
            },
        )
    response = await client.get(f"/api/v1/history?dog_id={dog_a}", headers=user_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert {item["dog_id"] for item in response.json()["items"]} == {dog_a}


async def test_history_filter_by_behavior(client: AsyncClient, user_headers: dict) -> None:
    dog_id = await create_dog(client, user_headers)
    media_id = await upload_media(client, user_headers)
    # audio with BARK yields ATTENTION_SEEKING
    await client.post(
        "/api/v1/analyses",
        headers=user_headers,
        json={
            "dog_id": dog_id,
            "input_type": "AUDIO",
            "media_ids": [media_id],
            "sound_category": "BARK",
            "idempotency_key": f"beh-f-{uuid.uuid4().hex[:6]}",
        },
    )
    response = await client.get("/api/v1/history?behavior=ATTENTION_SEEKING", headers=user_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1
    response = await client.get("/api/v1/history?behavior=PLAYFUL", headers=user_headers)
    assert response.json()["total"] == 0


async def test_history_invalid_page_rejected(client: AsyncClient, user_headers: dict) -> None:
    response = await client.get("/api/v1/history?page=0", headers=user_headers)
    assert response.status_code == 422

    response = await client.get("/api/v1/history?page_size=0", headers=user_headers)
    assert response.status_code == 422


async def test_other_users_history_invisible(
    client: AsyncClient, user_headers: dict, other_headers: dict
) -> None:
    await _seed_analyses(client, user_headers, 2, f"priv-{uuid.uuid4().hex[:8]}")
    response = await client.get("/api/v1/history", headers=other_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 0
