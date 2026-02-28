"""Transaction endpoint tests — list, get, pagination, date filters."""
import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from tests.conftest import VALID_USER, auth_headers, create_account

_ACCOUNTS = "/api/v1/accounts"


async def _seed_balance_and_transfer(client, headers, from_id, to_id, amount="100.00"):
    from tests.conftest import TestSessionLocal
    from app.accounts.models import Account

    async with TestSessionLocal() as session:
        result = await session.execute(select(Account).where(Account.id == from_id))
        acct = result.scalar_one()
        acct.balance = Decimal("1000.00")
        await session.commit()

    resp = await client.post(
        "/api/v1/transfers",
        json={
            "from_account_id": from_id,
            "to_account_id": to_id,
            "amount": amount,
            "idempotency_key": str(uuid.uuid4()),
        },
        headers=headers,
    )
    assert resp.status_code == 201


# ── List transactions ─────────────────────────────────────────────────────────

async def test_list_transactions_empty(client: AsyncClient):
    headers = await auth_headers(client)
    account = await create_account(client, headers)

    resp = await client.get(f"{_ACCOUNTS}/{account['id']}/transactions/", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["transactions"] == []
    assert data["total"] == 0


async def test_list_transactions_after_transfer(client: AsyncClient):
    headers = await auth_headers(client)
    from_acct = await create_account(client, headers, "CHECKING")
    to_acct = await create_account(client, headers, "SAVINGS")

    await _seed_balance_and_transfer(client, headers, from_acct["id"], to_acct["id"], "200.00")

    resp = await client.get(
        f"{_ACCOUNTS}/{from_acct['id']}/transactions/", headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["transactions"][0]["transaction_type"] == "TRANSFER_OUT"
    assert Decimal(data["transactions"][0]["amount"]) == Decimal("200.00")


async def test_list_transactions_pagination(client: AsyncClient):
    headers = await auth_headers(client)
    from_acct = await create_account(client, headers)
    to_acct = await create_account(client, headers, "SAVINGS")

    # Create 5 transfers → 5 TRANSFER_OUT records on from_acct
    from tests.conftest import TestSessionLocal
    from app.accounts.models import Account

    async with TestSessionLocal() as session:
        result = await session.execute(select(Account).where(Account.id == from_acct["id"]))
        acct = result.scalar_one()
        acct.balance = Decimal("5000.00")
        await session.commit()

    for _ in range(5):
        await client.post(
            "/api/v1/transfers",
            json={
                "from_account_id": from_acct["id"],
                "to_account_id": to_acct["id"],
                "amount": "50.00",
                "idempotency_key": str(uuid.uuid4()),
            },
            headers=headers,
        )

    page1 = await client.get(
        f"{_ACCOUNTS}/{from_acct['id']}/transactions/?page=1&limit=3", headers=headers
    )
    page2 = await client.get(
        f"{_ACCOUNTS}/{from_acct['id']}/transactions/?page=2&limit=3", headers=headers
    )

    assert page1.json()["total"] == 5
    assert len(page1.json()["transactions"]) == 3
    assert len(page2.json()["transactions"]) == 2


async def test_list_transactions_requires_auth(client: AsyncClient):
    resp = await client.get(f"{_ACCOUNTS}/some-id/transactions/")
    assert resp.status_code == 403


async def test_list_transactions_other_users_account_forbidden(client: AsyncClient):
    from tests.conftest import SECOND_USER

    alice_headers = await auth_headers(client)
    bob_headers = await auth_headers(client, SECOND_USER)
    bob_account = await create_account(client, bob_headers)

    resp = await client.get(
        f"{_ACCOUNTS}/{bob_account['id']}/transactions/", headers=alice_headers
    )
    assert resp.status_code == 403


# ── Get single transaction ────────────────────────────────────────────────────

async def test_get_transaction_success(client: AsyncClient):
    headers = await auth_headers(client)
    from_acct = await create_account(client, headers)
    to_acct = await create_account(client, headers, "SAVINGS")
    await _seed_balance_and_transfer(client, headers, from_acct["id"], to_acct["id"])

    list_resp = await client.get(
        f"{_ACCOUNTS}/{from_acct['id']}/transactions/", headers=headers
    )
    txn_id = list_resp.json()["transactions"][0]["id"]

    resp = await client.get(
        f"{_ACCOUNTS}/{from_acct['id']}/transactions/{txn_id}", headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == txn_id


async def test_get_transaction_not_found(client: AsyncClient):
    headers = await auth_headers(client)
    account = await create_account(client, headers)

    resp = await client.get(
        f"{_ACCOUNTS}/{account['id']}/transactions/nonexistent", headers=headers
    )
    assert resp.status_code == 404
