from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.base_model import UUIDPrimaryKey, utc_now
from app.database import Base


class AuditLog(UUIDPrimaryKey, Base):
    """Immutable audit trail. Never updated or deleted."""

    __tablename__ = "audit_logs"

    user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    old_values: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    new_values: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    # No updated_at, no deleted_at — immutable record
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
