"""Auth endpoint tests — register, login, refresh, logout."""
import pytest
from httpx import AsyncClient

from tests.conftest import VALID_USER, register_and_login

_BASE = "/api/v1/auth"


# ── Register ──────────────────────────────────────────────────────────────────

async def test_register_success(client: AsyncClient):
    resp = await client.post(f"{_BASE}/register", json=VALID_USER)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == VALID_USER["email"]
    assert "user_id" in data
    # password must never be returned
    assert "password" not in data
    assert "hashed_password" not in data


async def test_register_duplicate_email(client: AsyncClient):
    await client.post(f"{_BASE}/register", json=VALID_USER)
    resp = await client.post(f"{_BASE}/register", json=VALID_USER)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "EMAIL_TAKEN"


async def test_register_password_too_short(client: AsyncClient):
    resp = await client.post(f"{_BASE}/register", json={**VALID_USER, "password": "short"})
    assert resp.status_code == 422


async def test_register_invalid_email(client: AsyncClient):
    resp = await client.post(f"{_BASE}/register", json={**VALID_USER, "email": "not-an-email"})
    assert resp.status_code == 422


async def test_register_missing_full_name(client: AsyncClient):
    payload = {k: v for k, v in VALID_USER.items() if k != "full_name"}
    resp = await client.post(f"{_BASE}/register", json=payload)
    assert resp.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────

async def test_login_success(client: AsyncClient):
    await client.post(f"{_BASE}/register", json=VALID_USER)
    resp = await client.post(
        f"{_BASE}/login",
        json={"email": VALID_USER["email"], "password": VALID_USER["password"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient):
    await client.post(f"{_BASE}/register", json=VALID_USER)
    resp = await client.post(
        f"{_BASE}/login",
        json={"email": VALID_USER["email"], "password": "WrongPassword!"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"


async def test_login_nonexistent_user(client: AsyncClient):
    resp = await client.post(
        f"{_BASE}/login",
        json={"email": "ghost@example.com", "password": "SomePass1!"},
    )
    assert resp.status_code == 401


async def test_login_invalid_email_format(client: AsyncClient):
    resp = await client.post(
        f"{_BASE}/login", json={"email": "bad-email", "password": "SomePass1!"}
    )
    assert resp.status_code == 422


# ── Refresh ───────────────────────────────────────────────────────────────────

async def test_refresh_returns_new_access_token(client: AsyncClient):
    tokens = await register_and_login(client)
    resp = await client.post(
        f"{_BASE}/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    # Verify the returned token is a valid JWT (3-part structure)
    assert len(data["access_token"].split(".")) == 3


async def test_refresh_invalid_token(client: AsyncClient):
    resp = await client.post(f"{_BASE}/refresh", json={"refresh_token": "garbage-token"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_REFRESH_TOKEN"


# ── Logout ────────────────────────────────────────────────────────────────────

async def test_logout_revokes_refresh_token(client: AsyncClient):
    tokens = await register_and_login(client)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.post(
        f"{_BASE}/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers=headers,
    )
    assert resp.status_code == 204

    # Revoked token must no longer work
    resp = await client.post(
        f"{_BASE}/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert resp.status_code == 401


async def test_logout_requires_auth(client: AsyncClient):
    tokens = await register_and_login(client)
    resp = await client.post(
        f"{_BASE}/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    assert resp.status_code == 401


# ── Protected route — token validation ───────────────────────────────────────

async def test_protected_route_no_token(client: AsyncClient):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401


async def test_protected_route_malformed_token(client: AsyncClient):
    resp = await client.get(
        "/api/v1/users/me", headers={"Authorization": "Bearer not.a.jwt"}
    )
    assert resp.status_code == 401
