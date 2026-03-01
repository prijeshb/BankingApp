import hashlib
import random
import string
from datetime import date, datetime, timezone
from dateutil.relativedelta import relativedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cards.models import Card, CardStatus, CardType
from app.common.exceptions import OwnershipError, ResourceNotFoundError
from app.common.logging import get_logger

logger = get_logger(__name__)


def _generate_card_number() -> str:
    return "".join(random.choices(string.digits, k=16))


def _mask_card_number(number: str) -> str:
    return f"**** **** **** {number[-4:]}"


def _hash_card_number(number: str) -> str:
    return hashlib.sha256(number.encode()).hexdigest()


async def create_card(
    db: AsyncSession, account_id: str, card_type: CardType
) -> Card:
    raw_number = _generate_card_number()
    expiry = date.today().replace(day=1)
    # 3-year expiry, last day of that month
    expiry = (expiry + relativedelta(years=3, months=1)) - relativedelta(days=1)

    card = Card(
        account_id=account_id,
        card_number_masked=_mask_card_number(raw_number),
        card_number_hash=_hash_card_number(raw_number),
        card_type=card_type,
        expiry_date=expiry,
    )
    db.add(card)
    await db.flush()
    logger.info("card_created", card_id=card.id, account_id=account_id)
    return card


async def list_cards(db: AsyncSession, account_id: str) -> list[Card]:
    result = await db.execute(
        select(Card).where(
            Card.account_id == account_id,
            Card.deleted_at.is_(None),
        )
    )
    return list(result.scalars().all())


async def get_card(
    db: AsyncSession, card_id: str, requesting_user_id: str
) -> Card:
    result = await db.execute(
        select(Card).where(Card.id == card_id, Card.deleted_at.is_(None))
    )
    card = result.scalar_one_or_none()
    if not card:
        raise ResourceNotFoundError("Card", card_id)

    # Verify ownership via account
    from app.accounts.service import get_account_by_id
    account = await get_account_by_id(db, card.account_id)
    if not account or account.owner_id != requesting_user_id:
        raise OwnershipError()

    return card


async def update_card_status(
    db: AsyncSession, card: Card, new_status: CardStatus
) -> Card:
    card.status = new_status
    await db.flush()
    logger.info("card_status_updated", card_id=card.id, status=new_status)
    return card


async def soft_delete_card(db: AsyncSession, card: Card) -> None:
    card.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.flush()
    logger.info("card_soft_deleted", card_id=card.id)
