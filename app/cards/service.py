import hashlib
import secrets
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cards.models import Card, CardStatus, CardType
from app.common.crypto import decrypt, encrypt
from app.common.exceptions import BankingException, InvalidCardStatusError, OwnershipError, ResourceNotFoundError
from app.common.logging import get_logger

logger = get_logger(__name__)


def _generate_card_number() -> str:
    # M-1: use secrets (cryptographically secure) instead of random
    return "".join(str(secrets.randbelow(10)) for _ in range(16))


def _mask_card_number(number: str) -> str:
    return f"**** **** **** {number[-4:]}"


def _hash_card_number(number: str) -> str:
    return hashlib.sha256(number.encode()).hexdigest()


def _generate_cvv() -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(3))


async def create_card(
    db: AsyncSession, account_id: str, card_type: CardType
) -> Card:
    raw_number = _generate_card_number()
    cvv = _generate_cvv()
    # H-2: use UTC date to be consistent with how all other timestamps are stored
    expiry = datetime.now(timezone.utc).date().replace(day=1)
    # 3-year expiry, last day of that month
    expiry = (expiry + relativedelta(years=3, months=1)) - relativedelta(days=1)

    card = Card(
        account_id=account_id,
        card_number_masked=_mask_card_number(raw_number),
        card_number_hash=_hash_card_number(raw_number),
        card_number_encrypted=encrypt(raw_number),
        cvv_encrypted=encrypt(cvv),
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
    # M-4: EXPIRED is a system-managed state; it cannot be set via the API
    if new_status == CardStatus.EXPIRED:
        raise InvalidCardStatusError("EXPIRED status cannot be set manually")
    # Deleted-entity guard: prevent status changes on expired cards
    if card.status == CardStatus.EXPIRED:
        raise InvalidCardStatusError("Cannot change the status of an expired card")
    card.status = new_status
    await db.flush()
    logger.info("card_status_updated", card_id=card.id, status=new_status)
    return card


async def reveal_card(
    db: AsyncSession,
    card_id: str,
    requesting_user_id: str,
    password: str,
) -> dict:
    """Verify user password then return decrypted card number and CVV."""
    from app.users.models import User
    from app.auth.service import verify_password
    from sqlalchemy import select as sa_select

    card = await get_card(db, card_id, requesting_user_id=requesting_user_id)

    if not card.card_number_encrypted or not card.cvv_encrypted:
        raise BankingException("Card details not available for this card", 404, "NOT_FOUND")

    # Load the user to verify their password
    result = await db.execute(sa_select(User).where(User.id == requesting_user_id))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        raise BankingException("Incorrect password", 401, "INVALID_PASSWORD")

    raw_number = decrypt(card.card_number_encrypted)
    cvv = decrypt(card.cvv_encrypted)
    # Format as groups of 4
    formatted_number = " ".join(raw_number[i:i+4] for i in range(0, 16, 4))
    expiry = card.expiry_date.strftime("%m/%y")

    return {"card_number": formatted_number, "cvv": cvv, "expiry_date": expiry}


async def soft_delete_card(db: AsyncSession, card: Card) -> None:
    card.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.flush()
    logger.info("card_soft_deleted", card_id=card.id)
