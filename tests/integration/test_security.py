"""
Security edge-case tests — OWASP-oriented.
Covers: deleted/inactive resource access, cross-user access control,
        password complexity, SQL injection payloads, XSS payloads,
        oversized inputs, and boundary conditions.
"""
import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.accounts.models import Account
from app.users.models import User
from tests.conftest import (
    SECOND_USER,
    VALID_USER,
    TestSessionLocal,
    auth_headers,
    create_account,
    register_and_login,
)

pytestmark = pytest.mark.asyncio

_AUTH = "/api/v1/auth"
_USERS = "/api/v1/users"
_ACCOUNTS = "/api/v1/accounts"
_TRANSFERS = "/api/v1/transfers"


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _seed_balance(account_id: str, amount: str):
    async with TestSessionLocal() as session:
        result = await session.execute(
            select(Account).where(Account.id == account_id)
        )
        acct = result.scalar_one()
        acct.balance = Decimal(amount)
        await session.commit()


async def _soft_delete_account(account_id: str):
    from datetime import datetime, timezone

    async with TestSessionLocal() as session:
        result = await session.execute(
            select(Account).where(Account.id == account_id)
        )
        acct = result.scalar_one()
        acct.deleted_at = datetime.now(timezone.utc)
        acct.is_active = False
        await session.commit()


async def _deactivate_account(account_id: str):
    async with TestSessionLocal() as session:
        result = await session.execute(
            select(Account).where(Account.id == account_id)
        )
        acct = result.scalar_one()
        acct.is_active = False
        await session.commit()


# ── A07: Password Complexity ────────────────────────────────────────────────


async def test_register_no_uppercase_rejected(client: AsyncClient):
    resp = await client.post(
        f"{_AUTH}/register",
        json={"email": "weak1@test.com", "password": "lowercase1!", "full_name": "T"},
    )
    assert resp.status_code == 422


async def test_register_no_lowercase_rejected(client: AsyncClient):
    resp = await client.post(
        f"{_AUTH}/register",
        json={"email": "weak2@test.com", "password": "UPPERCASE1!", "full_name": "T"},
    )
    assert resp.status_code == 422


async def test_register_no_digit_rejected(client: AsyncClient):
    resp = await client.post(
        f"{_AUTH}/register",
        json={"email": "weak3@test.com", "password": "NoDigits!!", "full_name": "T"},
    )
    assert resp.status_code == 422


async def test_register_no_special_char_rejected(client: AsyncClient):
    resp = await client.post(
        f"{_AUTH}/register",
        json={"email": "weak4@test.com", "password": "NoSpecial1A", "full_name": "T"},
    )
    assert resp.status_code == 422


async def test_register_strong_password_accepted(client: AsyncClient):
    resp = await client.post(
        f"{_AUTH}/register",
        json={"email": "strong@test.com", "password": "Strong1!xy", "full_name": "T"},
    )
    assert resp.status_code == 201


# ── Deleted User Operations ─────────────────────────────────────────────────


async def test_deleted_user_cannot_login(client: AsyncClient):
    """After soft-delete, user must not be able to log in."""
    tokens = await register_and_login(client)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Delete the user
    resp = await client.delete(f"{_USERS}/me", headers=headers)
    assert resp.status_code == 204

    # Attempt login with deleted user credentials
    resp = await client.post(
        f"{_AUTH}/login",
        json={"email": VALID_USER["email"], "password": VALID_USER["password"]},
    )
    assert resp.status_code in (401, 403, 404)


async def test_deleted_user_token_rejected(client: AsyncClient):
    """Tokens issued before deletion must be rejected after soft-delete."""
    headers = await auth_headers(client)

    # Delete the user
    await client.delete(f"{_USERS}/me", headers=headers)

    # Old token should no longer grant access
    resp = await client.get(f"{_USERS}/me", headers=headers)
    assert resp.status_code in (401, 403, 404)


# ── Deleted Account Operations ──────────────────────────────────────────────


async def test_get_deleted_account_returns_404(client: AsyncClient):
    headers = await auth_headers(client)
    account = await create_account(client, headers)
    await _soft_delete_account(account["id"])

    resp = await client.get(f"{_ACCOUNTS}/{account['id']}", headers=headers)
    assert resp.status_code == 404


async def test_transfer_from_deleted_account_rejected(client: AsyncClient):
    headers = await auth_headers(client)
    from_acct = await create_account(client, headers, "CHECKING")
    to_acct = await create_account(client, headers, "SAVINGS")
    await _seed_balance(from_acct["id"], "500.00")
    await _soft_delete_account(from_acct["id"])

    resp = await client.post(
        _TRANSFERS,
        json={
            "from_account_id": from_acct["id"],
            "to_account_id": to_acct["id"],
            "amount": "100.00",
            "idempotency_key": str(uuid.uuid4()),
        },
        headers=headers,
    )
    assert resp.status_code in (404, 422)


async def test_transfer_to_deleted_account_rejected(client: AsyncClient):
    headers = await auth_headers(client)
    from_acct = await create_account(client, headers, "CHECKING")
    to_acct = await create_account(client, headers, "SAVINGS")
    await _seed_balance(from_acct["id"], "500.00")
    await _soft_delete_account(to_acct["id"])

    resp = await client.post(
        _TRANSFERS,
        json={
            "from_account_id": from_acct["id"],
            "to_account_id": to_acct["id"],
            "amount": "100.00",
            "idempotency_key": str(uuid.uuid4()),
        },
        headers=headers,
    )
    assert resp.status_code in (404, 422)


async def test_issue_card_on_deleted_account_rejected(client: AsyncClient):
    headers = await auth_headers(client)
    account = await create_account(client, headers)
    await _soft_delete_account(account["id"])

    resp = await client.post(
        f"{_ACCOUNTS}/{account['id']}/cards",
        json={"card_type": "DEBIT"},
        headers=headers,
    )
    assert resp.status_code in (404, 422)


# ── Inactive Account Operations ─────────────────────────────────────────────


async def test_transfer_from_inactive_account_rejected(client: AsyncClient):
    headers = await auth_headers(client)
    from_acct = await create_account(client, headers, "CHECKING")
    to_acct = await create_account(client, headers, "SAVINGS")
    await _seed_balance(from_acct["id"], "500.00")
    await _deactivate_account(from_acct["id"])

    resp = await client.post(
        _TRANSFERS,
        json={
            "from_account_id": from_acct["id"],
            "to_account_id": to_acct["id"],
            "amount": "100.00",
            "idempotency_key": str(uuid.uuid4()),
        },
        headers=headers,
    )
    assert resp.status_code in (404, 422)


# ── A01: Broken Access Control — Cross-User ────────────────────────────────


async def test_cannot_view_another_users_account(client: AsyncClient):
    alice_headers = await auth_headers(client, VALID_USER)
    bob_headers = await auth_headers(client, SECOND_USER)

    bob_account = await create_account(client, bob_headers)

    resp = await client.get(
        f"{_ACCOUNTS}/{bob_account['id']}", headers=alice_headers
    )
    assert resp.status_code == 403


async def test_cannot_list_another_users_transactions(client: AsyncClient):
    alice_headers = await auth_headers(client, VALID_USER)
    bob_headers = await auth_headers(client, SECOND_USER)

    bob_account = await create_account(client, bob_headers)

    resp = await client.get(
        f"{_ACCOUNTS}/{bob_account['id']}/transactions/", headers=alice_headers
    )
    assert resp.status_code == 403


async def test_cannot_delete_another_users_account(client: AsyncClient):
    alice_headers = await auth_headers(client, VALID_USER)
    bob_headers = await auth_headers(client, SECOND_USER)

    bob_account = await create_account(client, bob_headers)

    resp = await client.delete(
        f"{_ACCOUNTS}/{bob_account['id']}", headers=alice_headers
    )
    assert resp.status_code == 403


async def test_cannot_issue_card_on_another_users_account(client: AsyncClient):
    alice_headers = await auth_headers(client, VALID_USER)
    bob_headers = await auth_headers(client, SECOND_USER)

    bob_account = await create_account(client, bob_headers)

    resp = await client.post(
        f"{_ACCOUNTS}/{bob_account['id']}/cards",
        json={"card_type": "DEBIT"},
        headers=alice_headers,
    )
    assert resp.status_code == 403


async def test_cannot_view_another_users_cards(client: AsyncClient):
    alice_headers = await auth_headers(client, VALID_USER)
    bob_headers = await auth_headers(client, SECOND_USER)

    bob_account = await create_account(client, bob_headers)

    # Issue a card on Bob's account
    await client.post(
        f"{_ACCOUNTS}/{bob_account['id']}/cards",
        json={"card_type": "DEBIT"},
        headers=bob_headers,
    )

    resp = await client.get(
        f"{_ACCOUNTS}/{bob_account['id']}/cards", headers=alice_headers
    )
    assert resp.status_code == 403


async def test_cannot_view_another_users_transfer(client: AsyncClient):
    """Alice cannot retrieve Bob's transfer by ID."""
    alice_headers = await auth_headers(client, VALID_USER)
    bob_headers = await auth_headers(client, SECOND_USER)

    bob_from = await create_account(client, bob_headers, "CHECKING")
    bob_to = await create_account(client, bob_headers, "SAVINGS")
    await _seed_balance(bob_from["id"], "500.00")

    transfer_resp = await client.post(
        _TRANSFERS,
        json={
            "from_account_id": bob_from["id"],
            "to_account_id": bob_to["id"],
            "amount": "100.00",
            "idempotency_key": str(uuid.uuid4()),
        },
        headers=bob_headers,
    )
    transfer_id = transfer_resp.json()["id"]

    resp = await client.get(f"{_TRANSFERS}/{transfer_id}", headers=alice_headers)
    assert resp.status_code == 403


# ── A03: Injection — SQL Injection Payloads ─────────────────────────────────


async def test_sql_injection_in_register_email(client: AsyncClient):
    resp = await client.post(
        f"{_AUTH}/register",
        json={
            "email": "'; DROP TABLE users; --",
            "password": "SecurePass1!",
            "full_name": "Hacker",
        },
    )
    # Should be rejected by email validation (not a valid email)
    assert resp.status_code == 422


async def test_sql_injection_in_login_email(client: AsyncClient):
    resp = await client.post(
        f"{_AUTH}/login",
        json={
            "email": "' OR '1'='1",
            "password": "anything",
        },
    )
    assert resp.status_code == 422


async def test_sql_injection_in_full_name(client: AsyncClient):
    resp = await client.post(
        f"{_AUTH}/register",
        json={
            "email": "sqli@test.com",
            "password": "SecurePass1!",
            "full_name": "'; DROP TABLE users; --",
        },
    )
    # Should succeed — the name is just stored as a string, not executed
    assert resp.status_code == 201

    # Verify the name is stored literally
    login = await client.post(
        f"{_AUTH}/login",
        json={"email": "sqli@test.com", "password": "SecurePass1!"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    me = await client.get(f"{_USERS}/me", headers=headers)
    assert me.json()["full_name"] == "'; DROP TABLE users; --"


async def test_sql_injection_in_account_id_path(client: AsyncClient):
    headers = await auth_headers(client)
    resp = await client.get(
        f"{_ACCOUNTS}/1' OR '1'='1", headers=headers
    )
    assert resp.status_code in (404, 422)


# ── XSS Payload Handling ───────────────────────────────────────────────────


async def test_xss_in_full_name_stored_literally(client: AsyncClient):
    xss = "<script>alert('xss')</script>"
    resp = await client.post(
        f"{_AUTH}/register",
        json={
            "email": "xss@test.com",
            "password": "SecurePass1!",
            "full_name": xss,
        },
    )
    assert resp.status_code == 201

    login = await client.post(
        f"{_AUTH}/login",
        json={"email": "xss@test.com", "password": "SecurePass1!"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    me = await client.get(f"{_USERS}/me", headers=headers)
    # API returns JSON — XSS is the frontend's concern. Backend stores literally.
    assert me.json()["full_name"] == xss


async def test_xss_in_transfer_description(client: AsyncClient):
    headers = await auth_headers(client)
    from_acct = await create_account(client, headers, "CHECKING")
    to_acct = await create_account(client, headers, "SAVINGS")
    await _seed_balance(from_acct["id"], "500.00")

    xss = "<img src=x onerror=alert(1)>"
    resp = await client.post(
        _TRANSFERS,
        json={
            "from_account_id": from_acct["id"],
            "to_account_id": to_acct["id"],
            "amount": "10.00",
            "idempotency_key": str(uuid.uuid4()),
            "description": xss,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["description"] == xss  # stored literally, not executed


# ── Oversized & Boundary Inputs ─────────────────────────────────────────────


async def test_oversized_full_name_rejected(client: AsyncClient):
    resp = await client.post(
        f"{_AUTH}/register",
        json={
            "email": "long@test.com",
            "password": "SecurePass1!",
            "full_name": "A" * 300,  # max_length=255
        },
    )
    assert resp.status_code == 422


async def test_oversized_password_rejected(client: AsyncClient):
    resp = await client.post(
        f"{_AUTH}/register",
        json={
            "email": "longpw@test.com",
            "password": "Aa1!" + "x" * 100,  # max_length=100
            "full_name": "Test",
        },
    )
    assert resp.status_code == 422


async def test_duplicate_email_rejected(client: AsyncClient):
    await register_and_login(client)
    resp = await client.post(
        f"{_AUTH}/register",
        json=VALID_USER,
    )
    assert resp.status_code in (400, 409, 422)


# ── Account Edge Cases ──────────────────────────────────────────────────────


async def test_delete_account_with_balance_rejected(client: AsyncClient):
    headers = await auth_headers(client)
    account = await create_account(client, headers)
    await _seed_balance(account["id"], "100.00")

    resp = await client.delete(f"{_ACCOUNTS}/{account['id']}", headers=headers)
    assert resp.status_code == 422


async def test_nonexistent_account_returns_404(client: AsyncClient):
    headers = await auth_headers(client)
    resp = await client.get(
        f"{_ACCOUNTS}/{uuid.uuid4()}", headers=headers
    )
    assert resp.status_code == 404


# ── Update Deleted User Profile ─────────────────────────────────────────────


async def test_update_profile_after_delete_rejected(client: AsyncClient):
    headers = await auth_headers(client)
    await client.delete(f"{_USERS}/me", headers=headers)

    resp = await client.put(
        f"{_USERS}/me",
        json={"full_name": "Ghost"},
        headers=headers,
    )
    assert resp.status_code in (401, 403, 404)
