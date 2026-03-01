from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounts import service
from app.accounts.schemas import AccountListResponse, AccountResponse, CreateAccountRequest
from app.audit.service import log_action
from app.auth.dependencies import get_current_user
from app.common.types import UUIDPath
from app.database import get_db
from app.users.models import User

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    request: Request,
    body: CreateAccountRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = await service.create_account(
        db,
        owner_id=current_user.id,
        account_type=body.account_type,
        currency=body.currency,
    )
    await log_action(
        db,
        action="account.created",
        resource_type="Account",
        resource_id=account.id,
        user_id=current_user.id,
        new_values={"account_type": body.account_type, "currency": body.currency},
        ip_address=request.client.host if request.client else None,
    )
    return AccountResponse.model_validate(account)


@router.get("/", response_model=AccountListResponse)
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    accounts = await service.list_accounts(db, owner_id=current_user.id)
    return AccountListResponse(
        accounts=[AccountResponse.model_validate(a) for a in accounts],
        total=len(accounts),
    )


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: UUIDPath,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = await service.get_account(db, account_id, owner_id=current_user.id)
    return AccountResponse.model_validate(account)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    request: Request,
    account_id: UUIDPath,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = await service.get_account(db, account_id, owner_id=current_user.id)
    await service.soft_delete_account(db, account)
    await log_action(
        db,
        action="account.deleted",
        resource_type="Account",
        resource_id=account_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
