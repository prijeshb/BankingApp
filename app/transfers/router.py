from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import log_action
from app.auth.dependencies import get_current_user
from app.database import get_db
from app.transactions.schemas import CreateTransferRequest, TransferResponse
from app.transfers import service
from app.users.models import User

router = APIRouter(prefix="/api/v1/transfers", tags=["transfers"])


@router.post("/", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    body: CreateTransferRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transfer = await service.create_transfer(
        db,
        from_account_id=body.from_account_id,
        to_account_id=body.to_account_id,
        amount=body.amount,
        idempotency_key=body.idempotency_key,
        requesting_user_id=current_user.id,
        description=body.description,
    )
    await log_action(
        db,
        action="transfer.completed",
        resource_type="Transfer",
        resource_id=transfer.id,
        user_id=current_user.id,
        new_values={
            "from_account_id": body.from_account_id,
            "to_account_id": body.to_account_id,
            "amount": str(body.amount),
        },
    )
    return TransferResponse.model_validate(transfer)


@router.get("/{transfer_id}", response_model=TransferResponse)
async def get_transfer(
    transfer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transfer = await service.get_transfer(db, transfer_id, requesting_user_id=current_user.id)
    return TransferResponse.model_validate(transfer)
