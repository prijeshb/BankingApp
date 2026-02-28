import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.base_model import TimestampMixin, UUIDPrimaryKey
from app.database import Base

if TYPE_CHECKING:
    from app.cards.models import Card
    from app.transactions.models import Transaction
    from app.users.models import User


class AccountType(str, enum.Enum):
    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"


class Account(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "accounts"

    account_number: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    account_type: Mapped[AccountType] = mapped_column(SAEnum(AccountType), nullable=False)
    # Decimal(18, 4) — never float
    balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, default=Decimal("0.0000")
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped["User"] = relationship(back_populates="accounts")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account")
    cards: Mapped[list["Card"]] = relationship(back_populates="account")
