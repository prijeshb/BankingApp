from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import ResourceNotFoundError
from app.transactions.models import Transaction, TransactionStatus, TransactionType


async def list_transactions(
    db: AsyncSession,
    account_id: str,
    page: int = 1,
    limit: int = 20,
    start_date: date | None = None,
    end_date: date | None = None,
) -> tuple[list[Transaction], int]:
    query = select(Transaction).where(Transaction.account_id == account_id)

    # Naive UTC — SQLite stores datetimes without timezone info
    if start_date:
        query = query.where(
            Transaction.created_at >= datetime(start_date.year, start_date.month, start_date.day)
        )
    if end_date:
        end_dt = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
        query = query.where(Transaction.created_at <= end_dt)

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    query = query.order_by(Transaction.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all()), total


async def get_transaction(
    db: AsyncSession, transaction_id: str, account_id: str
) -> Transaction:
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.account_id == account_id,
        )
    )
    txn = result.scalar_one_or_none()
    if not txn:
        raise ResourceNotFoundError("Transaction", transaction_id)
    return txn


async def create_transaction(
    db: AsyncSession,
    account_id: str,
    idempotency_key: str,
    transaction_type: TransactionType,
    amount: Decimal,
    balance_after: Decimal,
    description: str | None = None,
    reference_id: str | None = None,
) -> Transaction:
    txn = Transaction(
        idempotency_key=idempotency_key,
        account_id=account_id,
        transaction_type=transaction_type,
        amount=amount,
        balance_after=balance_after,
        description=description,
        reference_id=reference_id,
        status=TransactionStatus.COMPLETED,
    )
    db.add(txn)
    await db.flush()
    return txn
