"""Phase 4 migration — knowledge graph tables.

Revision ID: 004
Creates: concept_entities, resource_entities, concept_relations with indexes.

Revises: 003
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create knowledge graph tables."""
    op.create_table(
        "concept_entities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("canonical_name", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("metadata", postgresql.JSONB),
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
            "canonical_name",
            "entity_type",
            name="uq_concept_entities_canonical_type",
        ),
    )
    op.create_index("idx_concept_entities_type", "concept_entities", ["entity_type"])
    op.create_index("idx_concept_entities_canonical", "concept_entities", ["canonical_name"])

    op.create_table(
        "resource_entities",
        sa.Column(
            "resource_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resources.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "entity_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("concept_entities.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
    )

    op.create_table(
        "concept_relations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "source_entity_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("concept_entities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_entity_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("concept_entities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("relation_type", sa.String(50), nullable=False),
        sa.Column("weight", sa.Float, nullable=False, server_default="1.0"),
        sa.Column(
            "source_resource_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resources.id", ondelete="SET NULL"),
        ),
        sa.Column("generated_by", sa.String(50), nullable=False, server_default="ollama"),
        sa.Column("metadata", postgresql.JSONB),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "source_entity_id",
            "target_entity_id",
            "relation_type",
            name="uq_concept_relations_src_dst_type",
        ),
    )
    op.create_index("idx_concept_relations_source", "concept_relations", ["source_entity_id"])
    op.create_index("idx_concept_relations_target", "concept_relations", ["target_entity_id"])


def downgrade() -> None:
    """Drop knowledge graph tables in reverse dependency order."""
    op.drop_index("idx_concept_relations_target", table_name="concept_relations")
    op.drop_index("idx_concept_relations_source", table_name="concept_relations")
    op.drop_table("concept_relations")
    op.drop_table("resource_entities")
    op.drop_index("idx_concept_entities_canonical", table_name="concept_entities")
    op.drop_index("idx_concept_entities_type", table_name="concept_entities")
    op.drop_table("concept_entities")
