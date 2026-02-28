from datetime import datetime, timezone
from typing import Any, Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.common.logging import get_logger

logger = get_logger(__name__)


async def log_action(
    db: AsyncSession,
    action: str,
    resource_type: str,
    resource_id: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    old_values: Optional[dict[str, Any]] = None,
    new_values: Optional[dict[str, Any]] = None,
) -> None:
    ctx = structlog.contextvars.get_contextvars()
    correlation_id = ctx.get("correlation_id", "unknown")

    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        correlation_id=correlation_id,
        old_values=old_values,
        new_values=new_values,
    )
    db.add(entry)
    await db.flush()

    logger.info(
        "audit_log",
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
    )
