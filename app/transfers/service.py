from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounts.models import Account
from app.accounts.service import get_account_by_id
from app.common.exceptions import (
    AccountInactiveError,
    BankingException,
    DuplicateIdempotencyKeyError,
    InsufficientFundsError,
    OwnershipError,
    ResourceNotFoundError,
)
from app.common.logging import get_logger
from app.transactions.models import Transfer, TransactionType, TransferStatus
from app.transactions.service import create_transaction

logger = get_logger(__name__)


async def get_transfer(
    db: AsyncSession, transfer_id: str, requesting_user_id: str
) -> Transfer:
    result = await db.execute(
        select(Transfer).where(Transfer.id == transfer_id)
    )
    transfer = result.scalar_one_or_none()
    if not transfer:
        raise ResourceNotFoundError("Transfer", transfer_id)

    # Ownership: requesting user must own at least one of the accounts
    from_account = await get_account_by_id(db, transfer.from_account_id)
    to_account = await get_account_by_id(db, transfer.to_account_id)

    owns = (from_account and from_account.owner_id == requesting_user_id) or (
        to_account and to_account.owner_id == requesting_user_id
    )
    if not owns:
        raise OwnershipError()

    return transfer


async def create_transfer(
    db: AsyncSession,
    from_account_id: str,
    to_account_id: str,
    amount: Decimal,
    idempotency_key: str,
    requesting_user_id: str,
    description: str | None = None,
) -> Transfer:
    # Idempotency: return existing transfer if key already used
    existing = await db.execute(
        select(Transfer).where(Transfer.idempotency_key == idempotency_key)
    )
    if existing.scalar_one_or_none():
        raise DuplicateIdempotencyKeyError()

    # Resolve accounts
    from_account = await get_account_by_id(db, from_account_id)
    if not from_account:
        raise ResourceNotFoundError("Account", from_account_id)
    if from_account.owner_id != requesting_user_id:
        raise OwnershipError()

    to_account = await get_account_by_id(db, to_account_id)
    if not to_account:
        raise ResourceNotFoundError("Account", to_account_id)

    if not from_account.is_active:
        raise AccountInactiveError()
    if not to_account.is_active:
        raise AccountInactiveError()

    if from_account.balance < amount:
        raise InsufficientFundsError()

    # --- Atomic debit + credit ---
    from_account.balance = from_account.balance - amount
    to_account.balance = to_account.balance + amount
    await db.flush()

    debit_txn = await create_transaction(
        db,
        account_id=from_account_id,
        idempotency_key=f"{idempotency_key}:debit",
        transaction_type=TransactionType.TRANSFER_OUT,
        amount=amount,
        balance_after=from_account.balance,
        description=description,
    )

    credit_txn = await create_transaction(
        db,
        account_id=to_account_id,
        idempotency_key=f"{idempotency_key}:credit",
        transaction_type=TransactionType.TRANSFER_IN,
        amount=amount,
        balance_after=to_account.balance,
        description=description,
        reference_id=debit_txn.id,
    )

    # Update debit record with its counterpart reference
    debit_txn.reference_id = credit_txn.id
    await db.flush()

    transfer = Transfer(
        idempotency_key=idempotency_key,
        from_account_id=from_account_id,
        to_account_id=to_account_id,
        amount=amount,
        status=TransferStatus.COMPLETED,
        from_transaction_id=debit_txn.id,
        to_transaction_id=credit_txn.id,
        description=description,
    )
    db.add(transfer)
    await db.flush()

    logger.info(
        "transfer_completed",
        transfer_id=transfer.id,
        from_account=from_account_id,
        to_account=to_account_id,
        amount=str(amount),
    )
    return transfer
