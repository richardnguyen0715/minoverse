"""AiEnrichment ORM model — stores AI-generated enrichments for resources.

Each enrichment record represents one AI output (summary, tags, entities, etc.)
linked to a resource. The unique constraint on (resource_id, enrichment_type)
ensures idempotent upserts via ON CONFLICT DO UPDATE.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class AiEnrichment(Base):
    """AI-generated enrichment record for a resource.

    Each row captures one type of enrichment (e.g. concise summary, tags)
    produced by a specific model at a specific prompt version. The
    ``is_current`` flag marks the latest version for each (resource_id,
    enrichment_type) pair.
    """

    __tablename__ = "ai_enrichments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    resource_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"),
        nullable=False,
    )
    enrichment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    model_name: Mapped[str] = mapped_column(Text, nullable=False)
    model_version: Mapped[str | None] = mapped_column(Text)
    prompt_version: Mapped[str] = mapped_column(String(20), nullable=False, server_default="v1")
    processing_ms: Mapped[int | None] = mapped_column(Integer)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
