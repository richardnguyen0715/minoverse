"""VaultFile ORM model — filesystem indexing layer.

Tracks every markdown file in the vault, its sync status,
and hash for change detection.
"""
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class VaultFile(Base):
    """Filesystem indexing record for a vault markdown file.

    This is the lowest-level index — one row per file on disk.
    The vault filesystem is the canonical source of truth;
    this table is a projection of it.
    """

    __tablename__ = "vault_files"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    relative_path: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    absolute_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_type: Mapped[str | None] = mapped_column(String(50))
    file_hash: Mapped[str | None] = mapped_column(String(64))
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    # pending | indexed | error
    sync_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    last_modified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
