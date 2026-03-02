import re
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.transactions.models import TransactionStatus, TransactionType, TransferStatus

_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


class TransactionResponse(BaseModel):
    id: str
    transaction_type: TransactionType
    amount: Decimal
    balance_after: Decimal
    description: Optional[str]
    reference_id: Optional[str]
    status: TransactionStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    transactions: list[TransactionResponse]
    total: int
    page: int
    limit: int


class TransferResponse(BaseModel):
    id: str
    from_account_id: str
    to_account_id: str
    amount: Decimal
    status: TransferStatus
    description: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class CreateTransferRequest(BaseModel):
    from_account_id: str = Field(..., min_length=36, max_length=36)
    to_account_id: str = Field(..., min_length=36, max_length=36)
    amount: Decimal = Field(..., gt=0)
    idempotency_key: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=255)

    @field_validator("from_account_id", "to_account_id")
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        if not _UUID_RE.match(v):
            raise ValueError("Must be a valid UUID")
        return v

    def model_post_init(self, __context) -> None:
        if self.from_account_id == self.to_account_id:
            raise ValueError("from_account_id and to_account_id must differ")
