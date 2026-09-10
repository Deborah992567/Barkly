"""Analysis endpoint tests: lifecycle, media, idempotency, ownership."""

from __future__ import annotations

import uuid

from httpx import AsyncClient

from tests.conftest import assert_error_shape, create_dog, upload_media


def _audio_payload(dog_id: str, media_id: str, key: str) -> dict:
    return {
        "dog_id": dog_id,
        "input_type": "AUDIO",
        "media_ids": [media_id],
        "sound_category": "BARK",
        "duration_ms": 2500,
        "context": {"owner_presence": "HOME", "recent_play": True},
        "idempotency_key": key,
    }


async def test_audio_analysis_completes_with_placeholder_contract(
    client: AsyncClient, user_headers: dict
) -> None:
    dog_id = await create_dog(client, user_headers)
    media_id = await upload_media(client, user_headers)
    response = await client.post(
        "/api/v1/analyses",
        headers=user_headers,
        json=_audio_payload(dog_id, media_id, f"key-{uuid.uuid4().hex[:8]}"),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["result"] is not None
    assert body["result"]["is_placeholder"] is True
    assert body["result"]["provider"] == "development-placeholder"
    assert body["result"]["model_name"] == "barkly-placeholder"
    assert body["result"]["primary_behavior"] == "ATTENTION_SEEKING"
    assert body["result"]["detected_audio_category"] == "BARK"
    assert "not veterinary" in body["result"]["disclaimer"]
    assert body["result"]["observations"]
    assert body["media"][0]["media_id"] == media_id
    assert body["context"]["owner_presence"] == "HOME"
    assert body["failure"] is None


async def test_behavior_analysis_has_no_media(client: AsyncClient, user_headers: dict) -> None:
    dog_id = await create_dog(client, user_headers)
    response = await client.post(
        "/api/v1/analyses",
        headers=user_headers,
        json={
            "dog_id": dog_id,
            "input_type": "BEHAVIOR",
            "media_ids": [],
            "context": {"activity_state": "RESTING"},
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["media"] == []
    assert body["result"]["primary_behavior"] in {
        "RELAXED",
        "ALERT",
        "PLAYFUL",
        "EXCITED",
        "CURIOUS",
        "ATTENTION_SEEKING",
        "FEARFUL",
        "STRESSED",
        "AGGRESSIVE",
        "SUBMISSIVE",
        "RESTLESS",
        "UNKNOWN",
    }


async def test_idempotent_retry_returns_same_analysis(
    client: AsyncClient, user_headers: dict
) -> None:
    dog_id = await create_dog(client, user_headers)
    media_id = await upload_media(client, user_headers)
    payload = _audio_payload(dog_id, media_id, "stable-key-0001")
    first = await client.post("/api/v1/analyses", headers=user_headers, json=payload)
    second = await client.post("/api/v1/analyses", headers=user_headers, json=payload)
    assert first.status_code == 201 and second.status_code == 201
    assert first.json()["analysis_id"] == second.json()["analysis_id"]
    history = await client.get("/api/v1/history", headers=user_headers)
    assert history.json()["total"] == 1


async def test_analysis_requires_owned_dog(
    client: AsyncClient, user_headers: dict, other_headers: dict
) -> None:
    other_dog = await create_dog(client, other_headers)
    response = await client.post(
        "/api/v1/analyses",
        headers=user_headers,
        json={"dog_id": other_dog, "input_type": "BEHAVIOR", "media_ids": []},
    )
    assert response.status_code == 404
    assert_error_shape(response.json(), "DOG_NOT_FOUND")


async def test_analysis_rejects_foreign_media(
    client: AsyncClient, user_headers: dict, other_headers: dict
) -> None:
    dog_id = await create_dog(client, user_headers)
    foreign_media = await upload_media(client, other_headers)
    response = await client.post(
        "/api/v1/analyses",
        headers=user_headers,
        json={"dog_id": dog_id, "input_type": "AUDIO", "media_ids": [foreign_media]},
    )
    assert response.status_code == 404
    assert_error_shape(response.json(), "RESOURCE_NOT_FOUND")


async def test_get_analysis_scoped_to_owner(
    client: AsyncClient, user_headers: dict, other_headers: dict
) -> None:
    dog_id = await create_dog(client, user_headers)
    media_id = await upload_media(client, user_headers)
    created = await client.post(
        "/api/v1/analyses",
        headers=user_headers,
        json=_audio_payload(dog_id, media_id, f"key-{uuid.uuid4().hex[:8]}"),
    )
    analysis_id = created.json()["analysis_id"]

    fetched = await client.get(f"/api/v1/analyses/{analysis_id}", headers=user_headers)
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "COMPLETED"

    denied = await client.get(f"/api/v1/analyses/{analysis_id}", headers=other_headers)
    assert denied.status_code == 404
    assert_error_shape(denied.json(), "ANALYSIS_NOT_FOUND")


async def test_invalid_input_shape_rejected(client: AsyncClient, user_headers: dict) -> None:
    dog_id = await create_dog(client, user_headers)
    response = await client.post(
        "/api/v1/analyses",
        headers=user_headers,
        json={"dog_id": dog_id, "input_type": "AUDIO", "media_ids": []},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_provider_failure_returns_failed_status(
    client: AsyncClient, user_headers: dict, monkeypatch
) -> None:
    from app.ai.base import ProviderUnavailableError
    from app.ai.types import AnalysisInput, InferenceResult
    from app.domain.value_objects import ModelIdentity

    class FailingProvider:
        identity = ModelIdentity("test", "failing", "0.0.0-test")

        async def analyze(self, request: AnalysisInput) -> InferenceResult:
            raise ProviderUnavailableError("down")

        async def health(self) -> bool:
            return True

    monkeypatch.setattr("app.services.analyses.get_provider", lambda name: FailingProvider())
    dog_id = await create_dog(client, user_headers)
    response = await client.post(
        "/api/v1/analyses",
        headers=user_headers,
        json={"dog_id": dog_id, "input_type": "BEHAVIOR", "media_ids": []},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "FAILED"
    assert body["failure"]["code"] == "PROVIDER_UNAVAILABLE"
    assert body["result"] is None


async def test_unknown_idempotency_conflict_never_ignored(
    client: AsyncClient, user_headers: dict
) -> None:
    dog_id = await create_dog(client, user_headers)
    payload = {
        "dog_id": dog_id,
        "input_type": "BEHAVIOR",
        "media_ids": [],
        "idempotency_key": "not-valid chars !!",
    }
    response = await client.post("/api/v1/analyses", headers=user_headers, json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
