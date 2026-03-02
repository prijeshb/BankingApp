"""Unit tests for transfer input validation via Pydantic schemas."""
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.transactions.schemas import CreateTransferRequest


_UUID_A = "00000000-0000-4000-8000-000000000001"
_UUID_B = "00000000-0000-4000-8000-000000000002"


def _valid_payload(**overrides) -> dict:
    base = {
        "from_account_id": _UUID_A,
        "to_account_id": _UUID_B,
        "amount": Decimal("100.00"),
        "idempotency_key": "key-123",
    }
    return {**base, **overrides}


def test_valid_transfer_parses():
    req = CreateTransferRequest(**_valid_payload())
    assert req.amount == Decimal("100.00")
    assert req.from_account_id == _UUID_A


def test_same_account_rejected():
    with pytest.raises(ValueError, match="must differ"):
        CreateTransferRequest(**_valid_payload(from_account_id=_UUID_A, to_account_id=_UUID_A))


def test_zero_amount_rejected():
    with pytest.raises(ValueError):
        CreateTransferRequest(**_valid_payload(amount=Decimal("0")))


def test_negative_amount_rejected():
    with pytest.raises(ValueError):
        CreateTransferRequest(**_valid_payload(amount=Decimal("-50.00")))


def test_amount_precision_preserved():
    req = CreateTransferRequest(**_valid_payload(amount=Decimal("99.9999")))
    assert req.amount == Decimal("99.9999")


def test_description_optional():
    req = CreateTransferRequest(**_valid_payload())
    assert req.description is None

    req_with_desc = CreateTransferRequest(**_valid_payload(description="rent"))
    assert req_with_desc.description == "rent"
