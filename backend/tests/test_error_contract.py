"""Error-contract tests: envelope, request id propagation, unknown routes."""

from __future__ import annotations

import uuid

from httpx import AsyncClient


async def test_unknown_route_yields_standard_envelope(client: AsyncClient) -> None:
    response = await client.get("/api/v1/nope")
    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "NOT_FOUND"
    assert error["message"]
    assert error["request_id"]


async def test_validation_error_envelope(client: AsyncClient, user_headers: dict) -> None:
    response = await client.post("/api/v1/dogs", headers=user_headers, json={"name": ""})
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "details" in error
    assert error["request_id"]


async def test_unauthenticated_envelope(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    error = response.json()["error"]
    assert error["code"] == "UNAUTHENTICATED"
    assert error["request_id"]


async def test_client_request_id_is_propagated(client: AsyncClient) -> None:
    rid = str(uuid.uuid4())
    response = await client.get(
        "/api/v1/dogs", headers={"X-Request-Id": rid, "Authorization": "Bearer nope"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["request_id"] == rid


async def test_healthy_root_endpoints(client: AsyncClient) -> None:
    health = await client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"


async def test_invalid_request_id_is_regenerated(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/dogs",
        headers={"X-Request-Id": "not a valid uuid", "Authorization": "Bearer nope"},
    )
    assert response.status_code == 401
    rid = response.json()["error"]["request_id"]
    # middleware must substitute a fresh valid uuid instead of echoing garbage
    uuid.UUID(rid)
