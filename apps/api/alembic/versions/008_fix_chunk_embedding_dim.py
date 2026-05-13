"""Fix chunk_embeddings vector dimension: 1536 → 768 (nomic-embed-text).

LM Studio's text-embedding-nomic-embed-text-v1.5 returns 768-dimensional
vectors, not 1536. The original schema used 1536 (OpenAI convention).

Revision ID: 008
Revises: 007
"""
from collections.abc import Sequence

from alembic import op

revision: str = "008"
down_revision: str | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Change embedding column from vector(1536) to vector(768)."""
    op.execute("DROP INDEX IF EXISTS chunk_embedding_idx")
    op.execute("ALTER TABLE chunk_embeddings ALTER COLUMN embedding TYPE vector(768)")
    op.execute(
        "CREATE INDEX chunk_embedding_idx ON chunk_embeddings "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists=50)"
    )


def downgrade() -> None:
    """Revert to vector(1536)."""
    op.execute("DROP INDEX IF EXISTS chunk_embedding_idx")
    op.execute("ALTER TABLE chunk_embeddings ALTER COLUMN embedding TYPE vector(1536)")
    op.execute(
        "CREATE INDEX chunk_embedding_idx ON chunk_embeddings "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists=100)"
    )
