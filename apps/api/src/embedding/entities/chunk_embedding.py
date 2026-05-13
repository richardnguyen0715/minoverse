"""ChunkEmbedding ORM model — semantic vector layer.

Stores pgvector embeddings for resource chunks.
One embedding per chunk; the embedding_model column ensures
embeddings can be regenerated if the model changes.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base

# pgvector VECTOR type — imported conditionally to allow
# schema generation without the extension installed.
try:
    from pgvector.sqlalchemy import Vector  # type: ignore[import-untyped]
    _VECTOR_TYPE = Vector(1536)
except ImportError:
    from sqlalchemy import Text as _VECTOR_FALLBACK  # noqa: F401
    _VECTOR_TYPE = Text()  # type: ignore[assignment]


class ChunkEmbedding(Base):
    """Embedding vector for a resource chunk.

    Constraints:
        - chunk_id is a 1:1 FK to resource_chunks.id.
        - embedding dimensions must match the configured model.
        - Changing embedding_model requires re-generating all embeddings.
    """

    __tablename__ = "chunk_embeddings"

    chunk_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resource_chunks.id", ondelete="CASCADE"), primary_key=True
    )
    embedding: Mapped[object] = mapped_column(_VECTOR_TYPE, nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
