"""ResourceTag ORM model — hybrid manual + AI tagging junction."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class ResourceTag(Base):
    """Association between a resource and a tag.

    generated_by_ai distinguishes manual tags from AI-generated ones.
    confidence_score is set for AI-generated tags.
    """

    __tablename__ = "resource_tags"

    resource_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )
    generated_by_ai: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confidence_score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
