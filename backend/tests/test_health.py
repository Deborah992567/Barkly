"""Liveness/probes."""

from __future__ import annotations

from httpx import AsyncClient


async def test_health_liveness(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "barkly-api"
    assert payload["request_id"]


async def test_ready_readiness(client: AsyncClient) -> None:
    response = await client.get("/ready")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["checks"]["database"] == "ok"
