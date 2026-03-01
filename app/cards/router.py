from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounts.service import get_account
from app.audit.service import log_action
from app.auth.dependencies import get_current_user
from app.cards import service
from app.cards.schemas import CardListResponse, CardResponse, CardRevealRequest, CardRevealResponse, CreateCardRequest, UpdateCardStatusRequest
from app.common.types import UUIDPath
from app.database import get_db
from app.users.models import User

router = APIRouter(tags=["cards"])


@router.post(
    "/api/v1/accounts/{account_id}/cards",
    response_model=CardResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_card(
    request: Request,
    account_id: UUIDPath,
    body: CreateCardRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_account(db, account_id, owner_id=current_user.id)
    card = await service.create_card(db, account_id=account_id, card_type=body.card_type)
    await log_action(
        db,
        action="card.created",
        resource_type="Card",
        resource_id=card.id,
        user_id=current_user.id,
        new_values={"card_type": body.card_type, "account_id": account_id},
        ip_address=request.client.host if request.client else None,
    )
    return CardResponse.model_validate(card)


@router.get("/api/v1/accounts/{account_id}/cards", response_model=CardListResponse)
async def list_cards(
    account_id: UUIDPath,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_account(db, account_id, owner_id=current_user.id)
    cards = await service.list_cards(db, account_id=account_id)
    return CardListResponse(
        cards=[CardResponse.model_validate(c) for c in cards],
        total=len(cards),
    )


@router.get("/api/v1/cards/{card_id}", response_model=CardResponse)
async def get_card(
    card_id: UUIDPath,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    card = await service.get_card(db, card_id, requesting_user_id=current_user.id)
    return CardResponse.model_validate(card)


@router.patch("/api/v1/cards/{card_id}/status", response_model=CardResponse)
async def update_card_status(
    request: Request,
    card_id: UUIDPath,
    body: UpdateCardStatusRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    card = await service.get_card(db, card_id, requesting_user_id=current_user.id)
    old_status = card.status
    updated = await service.update_card_status(db, card, body.status)
    await log_action(
        db,
        action="card.status_updated",
        resource_type="Card",
        resource_id=card_id,
        user_id=current_user.id,
        old_values={"status": old_status},
        new_values={"status": body.status},
        ip_address=request.client.host if request.client else None,
    )
    return CardResponse.model_validate(updated)


@router.post("/api/v1/cards/{card_id}/reveal", response_model=CardRevealResponse)
async def reveal_card(
    card_id: UUIDPath,
    body: CardRevealRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await service.reveal_card(
        db,
        card_id=card_id,
        requesting_user_id=current_user.id,
        password=body.password,
    )
    return CardRevealResponse(**result)


@router.delete("/api/v1/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    request: Request,
    card_id: UUIDPath,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    card = await service.get_card(db, card_id, requesting_user_id=current_user.id)
    await service.soft_delete_card(db, card)
    await log_action(
        db,
        action="card.deleted",
        resource_type="Card",
        resource_id=card_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
