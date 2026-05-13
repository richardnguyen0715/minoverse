"""Phase 6 — sync_events table for event sourcing and CRDT prep.

Revision ID: 007
Revises: 006
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "007"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create Phase 6 sync_events table."""
    op.create_table(
        "sync_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column(
            "resource_id",
            UUID(as_uuid=True),
            sa.ForeignKey("resources.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("resource_path", sa.Text, nullable=True),
        sa.Column("operation_id", UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("device_id", sa.String(255), nullable=True),
        sa.Column("vector_clock", JSONB, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("payload", JSONB, nullable=True),
        sa.Column("applied", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_sync_events_event_type", "sync_events", ["event_type"])
    op.create_index("ix_sync_events_resource_id", "sync_events", ["resource_id"])
    op.create_index("ix_sync_events_applied", "sync_events", ["applied"])
    op.create_index("ix_sync_events_created_at", "sync_events", ["created_at"])


def downgrade() -> None:
    """Drop Phase 6 sync_events table."""
    op.drop_index("ix_sync_events_created_at", table_name="sync_events")
    op.drop_index("ix_sync_events_applied", table_name="sync_events")
    op.drop_index("ix_sync_events_resource_id", table_name="sync_events")
    op.drop_index("ix_sync_events_event_type", table_name="sync_events")
    op.drop_table("sync_events")
