from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from app.transactions.models import TransactionStatus, TransactionType, TransferStatus


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
    from_account_id: str
    to_account_id: str
    amount: Decimal
    idempotency_key: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}

    def model_post_init(self, __context) -> None:
        if self.amount <= Decimal("0"):
            raise ValueError("amount must be positive")
        if self.from_account_id == self.to_account_id:
            raise ValueError("from_account_id and to_account_id must differ")
