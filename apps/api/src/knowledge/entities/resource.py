"""Resource ORM model — universal knowledge object.

Every piece of knowledge (paper, video, article, note, etc.)
is represented as a Resource. Resources are always linked to
a VaultFile as the canonical source.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Resource(Base):
    """Universal knowledge object linked to a vault file.

    Resource types: paper, youtube_video, github_repo, article,
    documentation, tweet, facebook_post, tiktok_video,
    note, concept, daily_note.
    """

    __tablename__ = "resources"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    vault_file_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("vault_files.id", ondelete="SET NULL")
    )
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    canonical_title: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)
    canonical_url: Mapped[str | None] = mapped_column(Text)
    source_platform: Mapped[str | None] = mapped_column(String(100))
    author: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(10))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    saved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    thumbnail_url: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    semantic_hash: Mapped[str | None] = mapped_column(String(64))
    importance_score: Mapped[float | None] = mapped_column(Float)
    quality_score: Mapped[float | None] = mapped_column(Float)
    relevance_score: Mapped[float | None] = mapped_column(Float)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # "metadata" is reserved by SQLAlchemy DeclarativeBase; use the explicit
    # column name to keep the DB column as "metadata".
    extra_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
