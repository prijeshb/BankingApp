from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.accounts.schemas import AccountResponse
from app.transactions.schemas import TransactionResponse


class StatementPeriod(BaseModel):
    start_date: date
    end_date: date


class StatementResponse(BaseModel):
    account: AccountResponse
    period: StatementPeriod
    opening_balance: Decimal
    closing_balance: Decimal
    total_credits: Decimal
    total_debits: Decimal
    transaction_count: int
    transactions: list[TransactionResponse]
    generated_at: datetime
