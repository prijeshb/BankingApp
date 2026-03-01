import random
import string
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounts.models import Account, AccountType
from app.common.exceptions import OwnershipError, ResourceNotFoundError
from app.common.logging import get_logger

logger = get_logger(__name__)


def _generate_account_number() -> str:
    digits = "".join(random.choices(string.digits, k=10))
    return f"ACC{digits}"


async def create_account(
    db: AsyncSession,
    owner_id: str,
    account_type: AccountType,
    currency: str,
) -> Account:
    # Ensure uniqueness of the generated account number
    for _ in range(5):
        number = _generate_account_number()
        existing = await db.execute(
            select(Account).where(Account.account_number == number)
        )
        if not existing.scalar_one_or_none():
            break

    account = Account(
        account_number=number,
        account_type=account_type,
        currency=currency,
        owner_id=owner_id,
    )
    db.add(account)
    await db.flush()
    logger.info("account_created", account_id=account.id, owner_id=owner_id)
    return account


async def get_account(
    db: AsyncSession, account_id: str, owner_id: str
) -> Account:
    result = await db.execute(
        select(Account).where(
            Account.id == account_id,
            Account.deleted_at.is_(None),
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise ResourceNotFoundError("Account", account_id)
    if account.owner_id != owner_id:
        raise OwnershipError()
    return account


async def get_account_by_id(db: AsyncSession, account_id: str) -> Account | None:
    """Internal lookup without ownership check."""
    result = await db.execute(
        select(Account).where(
            Account.id == account_id,
            Account.deleted_at.is_(None),
            Account.is_active.is_(True),
        )
    )
    return result.scalar_one_or_none()


async def list_accounts(db: AsyncSession, owner_id: str) -> list[Account]:
    result = await db.execute(
        select(Account).where(
            Account.owner_id == owner_id,
            Account.deleted_at.is_(None),
        )
    )
    return list(result.scalars().all())


async def soft_delete_account(db: AsyncSession, account: Account) -> None:
    account.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    account.is_active = False
    await db.flush()
    logger.info("account_soft_deleted", account_id=account.id)
