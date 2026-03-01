from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounts.service import get_account
from app.auth.dependencies import get_current_user
from app.common.types import UUIDPath
from app.database import get_db
from app.transactions import service
from app.transactions.schemas import TransactionListResponse, TransactionResponse
from app.users.models import User

router = APIRouter(
    prefix="/api/v1/accounts/{account_id}/transactions",
    tags=["transactions"],
)


@router.get("/", response_model=TransactionListResponse)
async def list_transactions(
    account_id: UUIDPath,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if start_date and end_date and end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_date must be on or after start_date",
        )
    # Ownership check
    await get_account(db, account_id, owner_id=current_user.id)

    transactions, total = await service.list_transactions(
        db,
        account_id=account_id,
        page=page,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
    )
    return TransactionListResponse(
        transactions=[TransactionResponse.model_validate(t) for t in transactions],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    account_id: UUIDPath,
    transaction_id: UUIDPath,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_account(db, account_id, owner_id=current_user.id)
    txn = await service.get_transaction(db, transaction_id, account_id=account_id)
    return TransactionResponse.model_validate(txn)
