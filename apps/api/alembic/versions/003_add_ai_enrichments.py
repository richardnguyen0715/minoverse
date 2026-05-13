"""Phase 3 migration — ai_enrichments table.

Revision ID: 003
Creates: ai_enrichments with unique constraint on (resource_id, enrichment_type)
         and an index on resource_id.

Revises: 002
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the ai_enrichments table."""
    op.create_table(
        "ai_enrichments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "resource_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("enrichment_type", sa.String(50), nullable=False),
        sa.Column("content", postgresql.JSONB, nullable=False),
        sa.Column("model_name", sa.Text, nullable=False),
        sa.Column("model_version", sa.Text),
        sa.Column("prompt_version", sa.String(20), nullable=False, server_default="v1"),
        sa.Column("processing_ms", sa.Integer),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "resource_id",
            "enrichment_type",
            name="uq_ai_enrichments_resource_type",
        ),
    )
    op.create_index("ix_ai_enrichments_resource_id", "ai_enrichments", ["resource_id"])


def downgrade() -> None:
    """Drop the ai_enrichments table."""
    op.drop_index("ix_ai_enrichments_resource_id", table_name="ai_enrichments")
    op.drop_table("ai_enrichments")
