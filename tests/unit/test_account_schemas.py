"""Unit tests for account schema validation."""
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.accounts.schemas import CreateAccountRequest


def test_valid_checking_account():
    req = CreateAccountRequest(account_type="CHECKING", currency="USD")
    assert req.currency == "USD"


def test_valid_savings_account():
    req = CreateAccountRequest(account_type="SAVINGS", currency="GBP")
    assert req.account_type.value == "SAVINGS"


def test_currency_lowercase_rejected():
    with pytest.raises(ValidationError):
        CreateAccountRequest(account_type="CHECKING", currency="usd")


def test_currency_too_long_rejected():
    with pytest.raises(ValidationError):
        CreateAccountRequest(account_type="CHECKING", currency="USDD")


def test_invalid_account_type_rejected():
    with pytest.raises(ValidationError):
        CreateAccountRequest(account_type="CURRENT", currency="USD")


def test_default_currency_is_usd():
    req = CreateAccountRequest(account_type="CHECKING")
    assert req.currency == "USD"
