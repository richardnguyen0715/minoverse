"""WikiLink ORM model — Obsidian wiki-link graph."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class WikiLink(Base):
    """Directed wiki-link edge between two notes.

    Represents [[Target]] links extracted from markdown.
    resolved_resource_id is set when the target can be matched
    to a known resource.
    """

    __tablename__ = "wiki_links"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_note_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("notes.id", ondelete="CASCADE"), nullable=False
    )
    target_note_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("notes.id", ondelete="SET NULL")
    )
    anchor_text: Mapped[str | None] = mapped_column(Text)
    resolved_resource_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("resources.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
