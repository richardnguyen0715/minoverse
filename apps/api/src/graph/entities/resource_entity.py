"""ResourceEntity ORM model — junction table linking resources to concept entities."""
import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class ResourceEntity(Base):
    """Junction table: which resources mention a given concept entity."""

    __tablename__ = "resource_entities"

    resource_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("concept_entities.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
