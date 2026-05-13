"""ConceptEntity ORM model — semantic concept node in the knowledge graph."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class ConceptEntity(Base):
    """A named entity extracted from knowledge resources.

    Nodes in the semantic knowledge graph. Deduplicated by (canonical_name, entity_type).
    ``extra_metadata`` persists in the DB column named ``metadata``.
    """

    __tablename__ = "concept_entities"
    __table_args__ = (UniqueConstraint("canonical_name", "entity_type", name="uq_concept_entities_canonical_type"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    canonical_name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    extra_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
