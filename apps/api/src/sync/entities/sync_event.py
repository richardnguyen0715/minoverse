"""SyncEvent ORM model — persists all sync domain events for event sourcing."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class SyncEvent(Base):
    """An immutable event record for event sourcing and CRDT-based sync."""

    __tablename__ = "sync_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resources.id", ondelete="SET NULL"),
        nullable=True,
    )
    resource_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    operation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4)
    device_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vector_clock: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    applied: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
