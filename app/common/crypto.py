"""Symmetric encryption for sensitive card data (card number, CVV).

Key is derived from JWT_SECRET_KEY so no separate secret is needed.
Uses Fernet (AES-128-CBC + HMAC-SHA256) from the cryptography package
that is already a dependency via python-jose[cryptography].
"""
import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet


@lru_cache(maxsize=1)
def _get_fernet() -> Fernet:
    from app.config import settings
    # Derive a 32-byte key from JWT_SECRET_KEY, then base64-encode for Fernet
    raw = hashlib.sha256(settings.JWT_SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(raw))


def encrypt(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    return _get_fernet().decrypt(ciphertext.encode()).decode()
