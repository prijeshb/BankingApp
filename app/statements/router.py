from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounts.service import get_account
from app.auth.dependencies import get_current_user
from app.common.types import UUIDPath
from app.database import get_db
from app.statements import service
from app.statements.schemas import StatementResponse
from app.users.models import User

router = APIRouter(
    prefix="/api/v1/accounts/{account_id}/statements",
    tags=["statements"],
)


@router.get("/", response_model=StatementResponse)
async def get_statement(
    account_id: UUIDPath,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_date must be on or after start_date",
        )
    account = await get_account(db, account_id, owner_id=current_user.id)
    return await service.generate_statement(db, account, start_date, end_date)
