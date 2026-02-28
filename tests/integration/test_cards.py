"""Card endpoint tests — issue, list, get, status update, soft delete."""
import pytest
from httpx import AsyncClient

from tests.conftest import SECOND_USER, VALID_USER, auth_headers, create_account

_ACCOUNTS = "/api/v1/accounts"
_CARDS = "/api/v1/cards"


async def _issue_card(client: AsyncClient, headers: dict, account_id: str, card_type: str = "DEBIT") -> dict:
    resp = await client.post(
        f"{_ACCOUNTS}/{account_id}/cards",
        json={"card_type": card_type},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── Create ────────────────────────────────────────────────────────────────────

async def test_issue_card_success(client: AsyncClient):
    headers = await auth_headers(client)
    account = await create_account(client, headers)

    resp = await client.post(
        f"{_ACCOUNTS}/{account['id']}/cards",
        json={"card_type": "DEBIT"},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["card_type"] == "DEBIT"
    assert data["status"] == "ACTIVE"
    assert "card_number_masked" in data
    # Full card number must never be returned
    assert len(data["card_number_masked"]) <= 19
    assert "****" in data["card_number_masked"]
    assert "expiry_date" in data


async def test_issue_virtual_card(client: AsyncClient):
    headers = await auth_headers(client)
    account = await create_account(client, headers)
    card = await _issue_card(client, headers, account["id"], "VIRTUAL")
    assert card["card_type"] == "VIRTUAL"


async def test_issue_card_requires_auth(client: AsyncClient):
    resp = await client.post(f"{_ACCOUNTS}/some-id/cards", json={"card_type": "DEBIT"})
    assert resp.status_code == 403


async def test_issue_card_other_users_account_forbidden(client: AsyncClient):
    alice_headers = await auth_headers(client, VALID_USER)
    bob_headers = await auth_headers(client, SECOND_USER)

    bob_account = await create_account(client, bob_headers)

    resp = await client.post(
        f"{_ACCOUNTS}/{bob_account['id']}/cards",
        json={"card_type": "DEBIT"},
        headers=alice_headers,
    )
    assert resp.status_code == 403


# ── List ──────────────────────────────────────────────────────────────────────

async def test_list_cards_empty(client: AsyncClient):
    headers = await auth_headers(client)
    account = await create_account(client, headers)

    resp = await client.get(f"{_ACCOUNTS}/{account['id']}/cards", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["cards"] == []
    assert data["total"] == 0


async def test_list_cards_multiple(client: AsyncClient):
    headers = await auth_headers(client)
    account = await create_account(client, headers)

    await _issue_card(client, headers, account["id"], "DEBIT")
    await _issue_card(client, headers, account["id"], "VIRTUAL")

    resp = await client.get(f"{_ACCOUNTS}/{account['id']}/cards", headers=headers)
    assert resp.json()["total"] == 2


# ── Get ───────────────────────────────────────────────────────────────────────

async def test_get_card_success(client: AsyncClient):
    headers = await auth_headers(client)
    account = await create_account(client, headers)
    card = await _issue_card(client, headers, account["id"])

    resp = await client.get(f"{_CARDS}/{card['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == card["id"]


async def test_get_card_other_user_forbidden(client: AsyncClient):
    alice_headers = await auth_headers(client, VALID_USER)
    bob_headers = await auth_headers(client, SECOND_USER)

    bob_account = await create_account(client, bob_headers)
    bob_card = await _issue_card(client, bob_headers, bob_account["id"])

    resp = await client.get(f"{_CARDS}/{bob_card['id']}", headers=alice_headers)
    assert resp.status_code == 403


# ── Status update ─────────────────────────────────────────────────────────────

async def test_block_card(client: AsyncClient):
    headers = await auth_headers(client)
    account = await create_account(client, headers)
    card = await _issue_card(client, headers, account["id"])

    resp = await client.patch(
        f"{_CARDS}/{card['id']}/status",
        json={"status": "BLOCKED"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "BLOCKED"


async def test_reactivate_card(client: AsyncClient):
    headers = await auth_headers(client)
    account = await create_account(client, headers)
    card = await _issue_card(client, headers, account["id"])

    await client.patch(f"{_CARDS}/{card['id']}/status", json={"status": "BLOCKED"}, headers=headers)
    resp = await client.patch(
        f"{_CARDS}/{card['id']}/status", json={"status": "ACTIVE"}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ACTIVE"


async def test_update_card_status_invalid_value(client: AsyncClient):
    headers = await auth_headers(client)
    account = await create_account(client, headers)
    card = await _issue_card(client, headers, account["id"])

    resp = await client.patch(
        f"{_CARDS}/{card['id']}/status", json={"status": "INVALID"}, headers=headers
    )
    assert resp.status_code == 422


# ── Delete (soft) ─────────────────────────────────────────────────────────────

async def test_delete_card_success(client: AsyncClient):
    headers = await auth_headers(client)
    account = await create_account(client, headers)
    card = await _issue_card(client, headers, account["id"])

    resp = await client.delete(f"{_CARDS}/{card['id']}", headers=headers)
    assert resp.status_code == 204

    # Card should no longer be visible
    resp = await client.get(f"{_CARDS}/{card['id']}", headers=headers)
    assert resp.status_code == 404
