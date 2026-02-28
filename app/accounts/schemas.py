from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.accounts.models import AccountType


class CreateAccountRequest(BaseModel):
    account_type: AccountType
    currency: str = Field(default="USD", min_length=3, max_length=3, pattern="^[A-Z]{3}$")


class AccountResponse(BaseModel):
    id: str
    account_number: str
    account_type: AccountType
    balance: Decimal
    currency: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AccountListResponse(BaseModel):
    accounts: list[AccountResponse]
    total: int
