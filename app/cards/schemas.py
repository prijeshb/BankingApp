from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from app.cards.models import CardStatus, CardType


class CreateCardRequest(BaseModel):
    card_type: CardType = CardType.DEBIT


class CardResponse(BaseModel):
    id: str
    card_number_masked: str
    card_type: CardType
    status: CardStatus
    expiry_date: date
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateCardStatusRequest(BaseModel):
    status: CardStatus

    @field_validator("status")
    @classmethod
    def status_not_expired(cls, v: CardStatus) -> CardStatus:
        if v == CardStatus.EXPIRED:
            raise ValueError("EXPIRED status cannot be set manually")
        return v


class CardListResponse(BaseModel):
    cards: list[CardResponse]
    total: int
