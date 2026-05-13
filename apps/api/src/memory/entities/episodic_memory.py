"""EpisodicMemory ORM model — a distilled memory of a research session."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class EpisodicMemory(Base):
    """Compressed narrative memory distilled from a conversation session.

    Stores a title and content summary synthesised by the AI from the
    conversation turns. Optionally links to the source session and
    referenced resources.
    """

    __tablename__ = "episodic_memories"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    resource_ids: Mapped[list | None] = mapped_column(JSONB)
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("memory_sessions.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
