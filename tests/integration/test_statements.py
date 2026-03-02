"""Statement endpoint tests."""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from tests.conftest import VALID_USER, auth_headers, create_account

_ACCOUNTS = "/api/v1/accounts"


async def _fund_and_transfer(client, headers, from_id, to_id, amount="100.00"):
    from tests.conftest import TestSessionLocal
    from app.accounts.models import Account

    async with TestSessionLocal() as session:
        result = await session.execute(select(Account).where(Account.id == from_id))
        acct = result.scalar_one()
        acct.balance = Decimal("1000.00")
        await session.commit()

    await client.post(
        "/api/v1/transfers",
        json={
            "from_account_id": from_id,
            "to_account_id": to_id,
            "amount": amount,
            "idempotency_key": str(uuid.uuid4()),
        },
        headers=headers,
    )


async def test_statement_empty_period(client: AsyncClient):
    headers = await auth_headers(client)
    account = await create_account(client, headers)

    resp = await client.get(
        f"{_ACCOUNTS}/{account['id']}/statements/",
        params={"start_date": "2024-01-01", "end_date": "2024-01-31"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["transaction_count"] == 0
    assert Decimal(data["opening_balance"]) == Decimal("0.0000")
    assert Decimal(data["closing_balance"]) == Decimal("0.0000")
    assert Decimal(data["total_credits"]) == Decimal("0.0000")
    assert Decimal(data["total_debits"]) == Decimal("0.0000")


async def test_statement_with_transactions(client: AsyncClient):
    headers = await auth_headers(client)
    from_acct = await create_account(client, headers)
    to_acct = await create_account(client, headers, "SAVINGS")

    await _fund_and_transfer(client, headers, from_acct["id"], to_acct["id"], "300.00")

    today = datetime.now(timezone.utc).date().isoformat()  # UTC date to match stored timestamps
    resp = await client.get(
        f"{_ACCOUNTS}/{to_acct['id']}/statements/",
        params={"start_date": today, "end_date": today},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["transaction_count"] == 1
    assert Decimal(data["total_credits"]) == Decimal("300.00")
    assert Decimal(data["closing_balance"]) == Decimal("300.00")


async def test_statement_requires_auth(client: AsyncClient):
    resp = await client.get(
        f"{_ACCOUNTS}/00000000-0000-0000-0000-000000000000/statements/",
        params={"start_date": "2024-01-01", "end_date": "2024-01-31"},
    )
    assert resp.status_code in (401, 403)


async def test_statement_other_users_account_forbidden(client: AsyncClient):
    from tests.conftest import SECOND_USER

    alice_headers = await auth_headers(client)
    bob_headers = await auth_headers(client, SECOND_USER)
    bob_account = await create_account(client, bob_headers)

    resp = await client.get(
        f"{_ACCOUNTS}/{bob_account['id']}/statements/",
        params={"start_date": "2024-01-01", "end_date": "2024-01-31"},
        headers=alice_headers,
    )
    assert resp.status_code == 403


async def test_statement_missing_date_params(client: AsyncClient):
    headers = await auth_headers(client)
    account = await create_account(client, headers)

    resp = await client.get(
        f"{_ACCOUNTS}/{account['id']}/statements/", headers=headers
    )
    assert resp.status_code == 422
