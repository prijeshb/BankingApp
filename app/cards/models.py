import enum
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, Enum as SAEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.base_model import TimestampMixin, UUIDPrimaryKey
from app.database import Base

if TYPE_CHECKING:
    from app.accounts.models import Account


class CardType(str, enum.Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"
    VIRTUAL = "VIRTUAL"


class CardStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BLOCKED = "BLOCKED"
    EXPIRED = "EXPIRED"


class Card(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "cards"

    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("accounts.id"), nullable=False, index=True
    )
    # Only last 4 digits stored in plain text — PCI-DSS alignment
    card_number_masked: Mapped[str] = mapped_column(String(19), nullable=False)
    # SHA-256 of the full card number for lookup
    card_number_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    card_type: Mapped[CardType] = mapped_column(SAEnum(CardType), nullable=False)
    status: Mapped[CardStatus] = mapped_column(
        SAEnum(CardStatus), nullable=False, default=CardStatus.ACTIVE
    )
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    account: Mapped["Account"] = relationship(back_populates="cards")
