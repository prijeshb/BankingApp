"""
Transfer tests — the most critical financial path.
Covers: happy path, insufficient funds, same-account, duplicate idempotency key,
        ownership enforcement, non-existent accounts, balance consistency.
"""
import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import SECOND_USER, VALID_USER, auth_headers, create_account

_TRANSFERS = "/api/v1/transfers"
_ACCOUNTS = "/api/v1/accounts"


def _transfer_payload(
    from_id: str,
    to_id: str,
    amount: str = "100.00",
    key: str | None = None,
    description: str = "test transfer",
) -> dict:
    return {
        "from_account_id": from_id,
        "to_account_id": to_id,
        "amount": amount,
        "idempotency_key": key or str(uuid.uuid4()),
        "description": description,
    }


async def _seed_balance(client: AsyncClient, headers: dict, account_id: str, amount: str):
    """Perform an internal credit by creating a transfer FROM a second account.
    Simpler approach: create a savings account on the same user and transfer.
    Actually we need to seed funds — we'll use a separate user as sender
    for setup, but that's circular. Instead, create a second account on the
    same user, then we top it up through… we can't without an admin endpoint.

    For tests, we fund via a second user owning a pre-credited account.
    The simplest way: create a second test user, give them a second account,
    seed their balance via a known transfer from a 'bank' account, etc.

    Because the app has no admin credit endpoint, we test transfers with
    whatever balance arrives from setup. We seed by doing a credit directly
    via the DB session in conftest — but since we can't easily inject that,
    we instead use the accounts service directly.

    Practical workaround: we give each test account a starting balance of 0
    and use DB-level seeding via a direct INSERT in the test that needs it.
    """
    pass


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _setup_funded_transfer(client: AsyncClient, amount: str = "500.00"):
    """
    Returns (alice_headers, from_account, to_account) where from_account
    has been seeded with funds via a direct DB manipulation through a
    dedicated deposit endpoint stub (POST /api/v1/accounts/{id}/deposit).

    Since no admin deposit endpoint exists, we rely on seeding the DB
    directly in this helper using the override session.
    """
    from sqlalchemy.ext.asyncio import AsyncSession
    from tests.conftest import TestSessionLocal
    from app.accounts.models import Account

    alice_headers = await auth_headers(client, VALID_USER)
    from_account = await create_account(client, alice_headers, "CHECKING")
    to_account = await create_account(client, alice_headers, "SAVINGS")

    # Seed from_account balance directly in the test DB
    async with TestSessionLocal() as session:
        result = await session.execute(
            select(Account).where(Account.id == from_account["id"])
        )
        acct = result.scalar_one()
        acct.balance = Decimal(amount)
        await session.commit()

    return alice_headers, from_account, to_account


# ── Happy path ────────────────────────────────────────────────────────────────

async def test_transfer_success(client: AsyncClient):
    headers, from_acct, to_acct = await _setup_funded_transfer(client, "500.00")

    resp = await client.post(
        _TRANSFERS,
        json=_transfer_payload(from_acct["id"], to_acct["id"], "200.00"),
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "COMPLETED"
    assert data["from_account_id"] == from_acct["id"]
    assert data["to_account_id"] == to_acct["id"]
    assert Decimal(data["amount"]) == Decimal("200.00")


async def test_transfer_debits_sender_and_credits_receiver(client: AsyncClient):
    headers, from_acct, to_acct = await _setup_funded_transfer(client, "500.00")

    await client.post(
        _TRANSFERS,
        json=_transfer_payload(from_acct["id"], to_acct["id"], "150.00"),
        headers=headers,
    )

    # Verify balances via account detail
    from_resp = await client.get(f"{_ACCOUNTS}/{from_acct['id']}", headers=headers)
    to_resp = await client.get(f"{_ACCOUNTS}/{to_acct['id']}", headers=headers)

    assert Decimal(from_resp.json()["balance"]) == Decimal("350.00")
    assert Decimal(to_resp.json()["balance"]) == Decimal("150.00")


async def test_transfer_creates_transaction_records(client: AsyncClient):
    headers, from_acct, to_acct = await _setup_funded_transfer(client, "500.00")

    await client.post(
        _TRANSFERS,
        json=_transfer_payload(from_acct["id"], to_acct["id"], "100.00"),
        headers=headers,
    )

    from_txns = await client.get(
        f"{_ACCOUNTS}/{from_acct['id']}/transactions/", headers=headers
    )
    to_txns = await client.get(
        f"{_ACCOUNTS}/{to_acct['id']}/transactions/", headers=headers
    )

    assert from_txns.json()["total"] == 1
    assert from_txns.json()["transactions"][0]["transaction_type"] == "TRANSFER_OUT"

    assert to_txns.json()["total"] == 1
    assert to_txns.json()["transactions"][0]["transaction_type"] == "TRANSFER_IN"


async def test_get_transfer_by_id(client: AsyncClient):
    headers, from_acct, to_acct = await _setup_funded_transfer(client, "500.00")

    create_resp = await client.post(
        _TRANSFERS,
        json=_transfer_payload(from_acct["id"], to_acct["id"], "50.00"),
        headers=headers,
    )
    transfer_id = create_resp.json()["id"]

    resp = await client.get(f"{_TRANSFERS}/{transfer_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == transfer_id


# ── Financial edge cases ──────────────────────────────────────────────────────

async def test_transfer_insufficient_funds(client: AsyncClient):
    headers, from_acct, to_acct = await _setup_funded_transfer(client, "100.00")

    resp = await client.post(
        _TRANSFERS,
        json=_transfer_payload(from_acct["id"], to_acct["id"], "200.00"),
        headers=headers,
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INSUFFICIENT_FUNDS"


async def test_transfer_zero_amount_rejected(client: AsyncClient):
    headers, from_acct, to_acct = await _setup_funded_transfer(client, "500.00")

    resp = await client.post(
        _TRANSFERS,
        json=_transfer_payload(from_acct["id"], to_acct["id"], "0"),
        headers=headers,
    )
    assert resp.status_code == 422


async def test_transfer_negative_amount_rejected(client: AsyncClient):
    headers, from_acct, to_acct = await _setup_funded_transfer(client, "500.00")

    resp = await client.post(
        _TRANSFERS,
        json=_transfer_payload(from_acct["id"], to_acct["id"], "-50.00"),
        headers=headers,
    )
    assert resp.status_code == 422


async def test_transfer_same_account_rejected(client: AsyncClient):
    headers, from_acct, _ = await _setup_funded_transfer(client, "500.00")

    resp = await client.post(
        _TRANSFERS,
        json=_transfer_payload(from_acct["id"], from_acct["id"], "50.00"),
        headers=headers,
    )
    assert resp.status_code == 422


async def test_transfer_exact_balance_succeeds(client: AsyncClient):
    """Transferring the entire balance should succeed (not fail with INSUFFICIENT_FUNDS)."""
    headers, from_acct, to_acct = await _setup_funded_transfer(client, "100.00")

    resp = await client.post(
        _TRANSFERS,
        json=_transfer_payload(from_acct["id"], to_acct["id"], "100.00"),
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "COMPLETED"

    from_resp = await client.get(f"{_ACCOUNTS}/{from_acct['id']}", headers=headers)
    assert Decimal(from_resp.json()["balance"]) == Decimal("0.0000")


# ── Idempotency ───────────────────────────────────────────────────────────────

async def test_duplicate_idempotency_key_rejected(client: AsyncClient):
    headers, from_acct, to_acct = await _setup_funded_transfer(client, "500.00")
    key = str(uuid.uuid4())
    payload = _transfer_payload(from_acct["id"], to_acct["id"], "50.00", key=key)

    first = await client.post(_TRANSFERS, json=payload, headers=headers)
    assert first.status_code == 201

    second = await client.post(_TRANSFERS, json=payload, headers=headers)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "DUPLICATE_IDEMPOTENCY_KEY"

    # Balance must only have changed once
    from_resp = await client.get(f"{_ACCOUNTS}/{from_acct['id']}", headers=headers)
    assert Decimal(from_resp.json()["balance"]) == Decimal("450.00")


# ── Ownership enforcement ─────────────────────────────────────────────────────

async def test_transfer_from_another_users_account_rejected(client: AsyncClient):
    alice_headers = await auth_headers(client, VALID_USER)
    bob_headers = await auth_headers(client, SECOND_USER)

    bob_account = await create_account(client, bob_headers)
    alice_account = await create_account(client, alice_headers)

    # Seed Bob's account
    from sqlalchemy.ext.asyncio import AsyncSession
    from tests.conftest import TestSessionLocal
    from app.accounts.models import Account

    async with TestSessionLocal() as session:
        result = await session.execute(select(Account).where(Account.id == bob_account["id"]))
        acct = result.scalar_one()
        acct.balance = Decimal("500.00")
        await session.commit()

    # Alice tries to transfer from Bob's account
    resp = await client.post(
        _TRANSFERS,
        json=_transfer_payload(bob_account["id"], alice_account["id"], "100.00"),
        headers=alice_headers,
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


async def test_transfer_to_nonexistent_account_rejected(client: AsyncClient):
    headers, from_acct, _ = await _setup_funded_transfer(client, "500.00")

    resp = await client.post(
        _TRANSFERS,
        json=_transfer_payload(from_acct["id"], "nonexistent-id", "50.00"),
        headers=headers,
    )
    assert resp.status_code == 404


async def test_transfer_requires_auth(client: AsyncClient):
    resp = await client.post(
        _TRANSFERS,
        json={
            "from_account_id": "a",
            "to_account_id": "b",
            "amount": "10",
            "idempotency_key": "k",
        },
    )
    assert resp.status_code == 401
