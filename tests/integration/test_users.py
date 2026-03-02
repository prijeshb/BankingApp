import pytest
from httpx import AsyncClient

from tests.conftest import VALID_USER, auth_headers, register_and_login

pytestmark = pytest.mark.asyncio


# ── GET /me ──────────────────────────────────────────────────────────────────


async def test_get_me_returns_profile(client: AsyncClient):
    headers = await auth_headers(client)
    resp = await client.get("/api/v1/users/me", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == VALID_USER["email"]
    assert data["full_name"] == VALID_USER["full_name"]
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data


async def test_get_me_without_auth(client: AsyncClient):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code in (401, 403)


# ── PUT /me ──────────────────────────────────────────────────────────────────


async def test_update_full_name(client: AsyncClient):
    headers = await auth_headers(client)
    resp = await client.put(
        "/api/v1/users/me",
        json={"full_name": "Alice Updated"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Alice Updated"


async def test_update_phone_number(client: AsyncClient):
    headers = await auth_headers(client)
    resp = await client.put(
        "/api/v1/users/me",
        json={"phone_number": "+1234567890"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["phone_number"] == "+1234567890"


async def test_update_date_of_birth(client: AsyncClient):
    headers = await auth_headers(client)
    resp = await client.put(
        "/api/v1/users/me",
        json={"date_of_birth": "1990-01-15"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["date_of_birth"] == "1990-01-15"


async def test_update_empty_name_rejected(client: AsyncClient):
    headers = await auth_headers(client)
    resp = await client.put(
        "/api/v1/users/me",
        json={"full_name": ""},
        headers=headers,
    )
    assert resp.status_code == 422


async def test_update_without_auth(client: AsyncClient):
    resp = await client.put("/api/v1/users/me", json={"full_name": "No Auth"})
    assert resp.status_code in (401, 403)


# ── DELETE /me ───────────────────────────────────────────────────────────────


async def test_delete_me(client: AsyncClient):
    headers = await auth_headers(client)
    resp = await client.delete("/api/v1/users/me", headers=headers)
    assert resp.status_code == 204

    # Deleted user cannot access profile
    resp2 = await client.get("/api/v1/users/me", headers=headers)
    assert resp2.status_code in (401, 403, 404)


async def test_delete_without_auth(client: AsyncClient):
    resp = await client.delete("/api/v1/users/me")
    assert resp.status_code in (401, 403)
