"""Note ORM model — Obsidian-native note system."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Note(Base):
    """Obsidian-compatible note record.

    Note types: atomic_note, permanent_note, literature_note,
    fleeting_note, daily_note, concept_note.
    """

    __tablename__ = "notes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    vault_file_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("vault_files.id", ondelete="SET NULL")
    )
    title: Mapped[str | None] = mapped_column(Text)
    note_type: Mapped[str | None] = mapped_column(String(50))
    frontmatter: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
