from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.logging import get_logger
from app.users.models import User

logger = get_logger(__name__)


async def get_profile(user: User) -> User:
    return user


async def update_profile(
    db: AsyncSession,
    user: User,
    full_name: Optional[str],
    phone_number: Optional[str],
    date_of_birth=None,
) -> User:
    if full_name is not None:
        user.full_name = full_name
    if phone_number is not None:
        user.phone_number = phone_number
    if date_of_birth is not None:
        user.date_of_birth = date_of_birth

    await db.flush()
    logger.info("user_profile_updated", user_id=user.id)
    return user


async def soft_delete(db: AsyncSession, user: User) -> None:
    user.deleted_at = datetime.now(timezone.utc)
    user.is_active = False
    await db.flush()
    logger.info("user_soft_deleted", user_id=user.id)
