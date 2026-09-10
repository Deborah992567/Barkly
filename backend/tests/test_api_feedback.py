"""Feedback endpoint tests: happy path, validation, ownership, state machine."""

from __future__ import annotations

import uuid

from httpx import AsyncClient

from tests.conftest import assert_error_shape, create_dog, upload_media


async def _create_completed(client, headers, dog_id=None):
    if dog_id is None:
        dog_id = await create_dog(client, headers)
    media_id = await upload_media(client, headers)
    response = await client.post(
        "/api/v1/analyses",
        headers=headers,
        json={
            "dog_id": dog_id,
            "input_type": "AUDIO",
            "media_ids": [media_id],
            "sound_category": "BARK",
            "idempotency_key": f"fb-{uuid.uuid4().hex[:8]}",
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "COMPLETED"
    return response.json()["analysis_id"]


async def test_confirm_feedback(client: AsyncClient, user_headers: dict) -> None:
    analysis_id = await _create_completed(client, user_headers)
    response = await client.post(
        f"/api/v1/analyses/{analysis_id}/feedback",
        headers=user_headers,
        json={"verdict": "CONFIRMED"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["verdict"] == "CONFIRMED"
    assert body["predicted_behavior"] == "ATTENTION_SEEKING"
    assert body["corrected_behavior"] is None


async def test_correction_feedback(client: AsyncClient, user_headers: dict) -> None:
    analysis_id = await _create_completed(client, user_headers)
    response = await client.post(
        f"/api/v1/analyses/{analysis_id}/feedback",
        headers=user_headers,
        json={"verdict": "CORRECTED", "corrected_behavior": "ALERT"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["predicted_behavior"] == "ATTENTION_SEEKING"
    assert body["corrected_behavior"] == "ALERT"
    assert body["comment"] is None


async def test_feedback_multiple_submissions_allowed(
    client: AsyncClient, user_headers: dict
) -> None:
    analysis_id = await _create_completed(client, user_headers)
    for verdict in ("CONFIRMED", "CONFIRMED", "CORRECTED"):
        response = await client.post(
            f"/api/v1/analyses/{analysis_id}/feedback",
            headers=user_headers,
            json={
                "verdict": verdict,
                **({"corrected_behavior": "RELAXED"} if verdict == "CORRECTED" else {}),
            },
        )
        assert response.status_code == 201, response.text


async def test_feedback_requires_analysis_owner(
    client: AsyncClient, user_headers: dict, other_headers: dict
) -> None:
    analysis_id = await _create_completed(client, user_headers)
    response = await client.post(
        f"/api/v1/analyses/{analysis_id}/feedback",
        headers=other_headers,
        json={"verdict": "CONFIRMED"},
    )
    assert response.status_code == 404
    assert_error_shape(response.json(), "ANALYSIS_NOT_FOUND")


async def test_correction_without_behavior_rejected(
    client: AsyncClient, user_headers: dict
) -> None:
    analysis_id = await _create_completed(client, user_headers)
    response = await client.post(
        f"/api/v1/analyses/{analysis_id}/feedback",
        headers=user_headers,
        json={"verdict": "CORRECTED"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_feedback_on_missing_analysis_404(client: AsyncClient, user_headers: dict) -> None:
    response = await client.post(
        f"/api/v1/analyses/{uuid.uuid4()}/feedback",
        headers=user_headers,
        json={"verdict": "CONFIRMED"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ANALYSIS_NOT_FOUND"
