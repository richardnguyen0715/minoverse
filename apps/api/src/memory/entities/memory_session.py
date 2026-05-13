"""MemorySession ORM model — a copilot conversation session."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.memory.entities.memory_turn import MemoryTurn


class MemorySession(Base):
    """A named research/copilot conversation session.

    Groups related turns (question/answer pairs) together and can be
    distilled into an episodic memory.
    """

    __tablename__ = "memory_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    turns: Mapped[list[MemoryTurn]] = relationship(
        "MemoryTurn",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="MemoryTurn.created_at",
    )
