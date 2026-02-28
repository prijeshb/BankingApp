"""Unit tests for auth service — pure functions only, no DB required."""
from datetime import datetime, timezone

import pytest
from jose import jwt

from app.auth.service import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.config import settings


# ── Password hashing ──────────────────────────────────────────────────────────

def test_hash_password_produces_bcrypt_hash():
    hashed = hash_password("MySecret1!")
    assert hashed.startswith("$2b$")


def test_hash_password_is_not_reversible():
    hashed = hash_password("MySecret1!")
    assert "MySecret1!" not in hashed


def test_verify_password_correct():
    hashed = hash_password("CorrectPass!")
    assert verify_password("CorrectPass!", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("CorrectPass!")
    assert verify_password("WrongPass!", hashed) is False


def test_same_password_produces_different_hashes():
    """bcrypt salts must produce unique hashes per call."""
    h1 = hash_password("SamePassword1!")
    h2 = hash_password("SamePassword1!")
    assert h1 != h2
    # But both must verify correctly
    assert verify_password("SamePassword1!", h1)
    assert verify_password("SamePassword1!", h2)


# ── Access token ──────────────────────────────────────────────────────────────

def test_create_access_token_is_valid_jwt():
    token = create_access_token("user-123")
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"


def test_access_token_contains_expiry():
    token = create_access_token("user-123")
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert "exp" in payload
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    assert exp > datetime.now(timezone.utc)


def test_access_token_different_users_differ():
    t1 = create_access_token("user-1")
    t2 = create_access_token("user-2")
    assert t1 != t2


def test_access_token_wrong_key_fails():
    token = create_access_token("user-123")
    with pytest.raises(Exception):
        jwt.decode(token, "wrong-secret-key", algorithms=[settings.JWT_ALGORITHM])
