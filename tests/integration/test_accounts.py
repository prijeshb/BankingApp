"""Account endpoint tests — create, list, get, delete + ownership."""
import pytest
from httpx import AsyncClient

from tests.conftest import SECOND_USER, VALID_USER, auth_headers, create_account

_BASE = "/api/v1/accounts"


# ── Create ────────────────────────────────────────────────────────────────────

async def test_create_checking_account(client: AsyncClient):
    headers = await auth_headers(client)
    resp = await client.post(
        f"{_BASE}/", json={"account_type": "CHECKING", "currency": "USD"}, headers=headers
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["account_type"] == "CHECKING"
    assert data["currency"] == "USD"
    assert data["balance"] == "0.0000"
    assert data["account_number"].startswith("ACC")
    assert data["is_active"] is True


async def test_create_savings_account(client: AsyncClient):
    headers = await auth_headers(client)
    resp = await client.post(
        f"{_BASE}/", json={"account_type": "SAVINGS", "currency": "USD"}, headers=headers
    )
    assert resp.status_code == 201
    assert resp.json()["account_type"] == "SAVINGS"


async def test_create_account_requires_auth(client: AsyncClient):
    resp = await client.post(f"{_BASE}/", json={"account_type": "CHECKING", "currency": "USD"})
    assert resp.status_code == 403


async def test_create_account_invalid_type(client: AsyncClient):
    headers = await auth_headers(client)
    resp = await client.post(
        f"{_BASE}/", json={"account_type": "INVALID", "currency": "USD"}, headers=headers
    )
    assert resp.status_code == 422


async def test_create_account_invalid_currency(client: AsyncClient):
    headers = await auth_headers(client)
    resp = await client.post(
        f"{_BASE}/", json={"account_type": "CHECKING", "currency": "usd"}, headers=headers
    )
    assert resp.status_code == 422


# ── List ──────────────────────────────────────────────────────────────────────

async def test_list_accounts_empty(client: AsyncClient):
    headers = await auth_headers(client)
    resp = await client.get(f"{_BASE}/", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["accounts"] == []
    assert data["total"] == 0


async def test_list_accounts_returns_only_own(client: AsyncClient):
    alice_headers = await auth_headers(client, VALID_USER)
    bob_headers = await auth_headers(client, SECOND_USER)

    await create_account(client, alice_headers)
    await create_account(client, alice_headers)
    await create_account(client, bob_headers)

    resp = await client.get(f"{_BASE}/", headers=alice_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2


async def test_list_accounts_requires_auth(client: AsyncClient):
    resp = await client.get(f"{_BASE}/")
    assert resp.status_code == 403


# ── Get ───────────────────────────────────────────────────────────────────────

async def test_get_account_success(client: AsyncClient):
    headers = await auth_headers(client)
    account = await create_account(client, headers)

    resp = await client.get(f"{_BASE}/{account['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == account["id"]


async def test_get_account_not_found(client: AsyncClient):
    headers = await auth_headers(client)
    resp = await client.get(f"{_BASE}/nonexistent-id", headers=headers)
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


async def test_get_account_owned_by_other_user(client: AsyncClient):
    alice_headers = await auth_headers(client, VALID_USER)
    bob_headers = await auth_headers(client, SECOND_USER)

    bob_account = await create_account(client, bob_headers)

    resp = await client.get(f"{_BASE}/{bob_account['id']}", headers=alice_headers)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


# ── Delete (soft) ─────────────────────────────────────────────────────────────

async def test_delete_account_success(client: AsyncClient):
    headers = await auth_headers(client)
    account = await create_account(client, headers)

    resp = await client.delete(f"{_BASE}/{account['id']}", headers=headers)
    assert resp.status_code == 204

    # Deleted account should no longer appear
    resp = await client.get(f"{_BASE}/{account['id']}", headers=headers)
    assert resp.status_code == 404


async def test_delete_account_owned_by_other_user(client: AsyncClient):
    alice_headers = await auth_headers(client, VALID_USER)
    bob_headers = await auth_headers(client, SECOND_USER)

    bob_account = await create_account(client, bob_headers)

    resp = await client.delete(f"{_BASE}/{bob_account['id']}", headers=alice_headers)
    assert resp.status_code == 403
