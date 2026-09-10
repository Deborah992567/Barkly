"""Dog endpoint tests: CRUD, ownership, validation."""

from __future__ import annotations

from httpx import AsyncClient

from tests.conftest import assert_error_shape, create_dog


async def test_create_and_list_dogs(client: AsyncClient, user_headers: dict) -> None:
    response = await client.post(
        "/api/v1/dogs",
        headers=user_headers,
        json={"name": "Max", "breed": "Beagle", "sex": "MALE"},
    )
    assert response.status_code == 201
    dog = response.json()
    assert dog["name"] == "Max"
    assert dog["sex"] == "MALE"
    assert dog["date_of_birth"] is None

    listed = await client.get("/api/v1/dogs", headers=user_headers)
    assert listed.status_code == 200
    assert [d["id"] for d in listed.json()] == [dog["id"]]


async def test_dog_creation_without_breed(client: AsyncClient, user_headers: dict) -> None:
    response = await client.post("/api/v1/dogs", headers=user_headers, json={"name": "Unknown"})
    assert response.status_code == 201
    assert response.json()["breed"] is None


async def test_get_and_update_dog(client: AsyncClient, user_headers: dict) -> None:
    dog_id = await create_dog(client, user_headers)
    updated = await client.patch(
        f"/api/v1/dogs/{dog_id}",
        headers=user_headers,
        json={"name": "Bella", "notes": "Loves fetch"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Bella"
    assert updated.json()["notes"] == "Loves fetch"


async def test_empty_update_rejected(client: AsyncClient, user_headers: dict) -> None:
    dog_id = await create_dog(client, user_headers)
    response = await client.patch(f"/api/v1/dogs/{dog_id}", headers=user_headers, json={})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_delete_dog_with_no_history(client: AsyncClient, user_headers: dict) -> None:
    dog_id = await create_dog(client, user_headers)
    response = await client.delete(f"/api/v1/dogs/{dog_id}", headers=user_headers)
    assert response.status_code == 204


async def test_cross_user_dog_access_denied(
    client: AsyncClient, user_headers: dict, other_headers: dict
) -> None:
    dog_id = await create_dog(client, user_headers)
    get_resp = await client.get(f"/api/v1/dogs/{dog_id}", headers=other_headers)
    patch_resp = await client.patch(
        f"/api/v1/dogs/{dog_id}", headers=other_headers, json={"name": "Pwned"}
    )
    delete_resp = await client.delete(f"/api/v1/dogs/{dog_id}", headers=other_headers)
    for response in (get_resp, patch_resp, delete_resp):
        assert response.status_code == 404
        assert_error_shape(response.json(), "DOG_NOT_FOUND")


async def test_missing_dog_404(client: AsyncClient, user_headers: dict) -> None:
    import uuid

    response = await client.get(f"/api/v1/dogs/{uuid.uuid4()}", headers=user_headers)
    assert response.status_code == 404
    assert_error_shape(response.json(), "DOG_NOT_FOUND")


async def test_invalid_sex_rejected(client: AsyncClient, user_headers: dict) -> None:
    response = await client.post(
        "/api/v1/dogs", headers=user_headers, json={"name": "Max", "sex": "ALIEN"}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
