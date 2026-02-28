from datetime import date, datetime, timezone, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounts.models import Account
from app.statements.schemas import StatementPeriod, StatementResponse
from app.transactions.models import Transaction, TransactionType


async def generate_statement(
    db: AsyncSession,
    account: Account,
    start_date: date,
    end_date: date,
) -> StatementResponse:
    start_dt = datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc)
    end_dt = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=timezone.utc)

    # Opening balance: balance_after of the last transaction before start_date
    pre_result = await db.execute(
        select(Transaction)
        .where(
            Transaction.account_id == account.id,
            Transaction.created_at < start_dt,
        )
        .order_by(Transaction.created_at.desc())
        .limit(1)
    )
    pre_txn = pre_result.scalar_one_or_none()
    opening_balance = pre_txn.balance_after if pre_txn else Decimal("0.0000")

    # Transactions in the period
    result = await db.execute(
        select(Transaction)
        .where(
            Transaction.account_id == account.id,
            Transaction.created_at >= start_dt,
            Transaction.created_at <= end_dt,
        )
        .order_by(Transaction.created_at.asc())
    )
    transactions = list(result.scalars().all())

    credit_types = {TransactionType.CREDIT, TransactionType.TRANSFER_IN}
    total_credits = sum(
        t.amount for t in transactions if t.transaction_type in credit_types
    ) or Decimal("0.0000")
    total_debits = sum(
        t.amount for t in transactions if t.transaction_type not in credit_types
    ) or Decimal("0.0000")

    closing_balance = transactions[-1].balance_after if transactions else opening_balance

    from app.accounts.schemas import AccountResponse
    from app.transactions.schemas import TransactionResponse

    return StatementResponse(
        account=AccountResponse.model_validate(account),
        period=StatementPeriod(start_date=start_date, end_date=end_date),
        opening_balance=opening_balance,
        closing_balance=closing_balance,
        total_credits=total_credits,
        total_debits=total_debits,
        transaction_count=len(transactions),
        transactions=[TransactionResponse.model_validate(t) for t in transactions],
        generated_at=datetime.now(timezone.utc),
    )
