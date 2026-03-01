from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import log_action
from app.auth.dependencies import get_current_user
from app.database import get_db
from app.users import service
from app.users.models import User
from app.users.schemas import UpdateUserRequest, UserResponse

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_me(
    request: Request,
    body: UpdateUserRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = await service.update_profile(
        db,
        current_user,
        full_name=body.full_name,
        phone_number=body.phone_number,
        date_of_birth=body.date_of_birth,
    )
    await log_action(
        db,
        action="user.profile_updated",
        resource_type="User",
        resource_id=current_user.id,
        user_id=current_user.id,
        new_values={k: str(v) for k, v in body.model_dump(exclude_none=True).items()},
        ip_address=request.client.host if request.client else None,
    )
    return UserResponse.model_validate(updated)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await service.soft_delete(db, current_user)
    await log_action(
        db,
        action="user.deleted",
        resource_type="User",
        resource_id=current_user.id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
