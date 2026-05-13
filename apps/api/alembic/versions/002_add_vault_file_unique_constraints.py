"""Add unique constraints on vault_file_id in resources and notes.

Revision ID: 002
Required for ON CONFLICT DO UPDATE upserts in Phase 1 repositories.

Revises: 001
"""
from collections.abc import Sequence

from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add unique constraints on vault_file_id."""
    op.create_unique_constraint(
        "uq_resources_vault_file_id", "resources", ["vault_file_id"]
    )
    op.create_unique_constraint(
        "uq_notes_vault_file_id", "notes", ["vault_file_id"]
    )


def downgrade() -> None:
    """Remove unique constraints on vault_file_id."""
    op.drop_constraint("uq_resources_vault_file_id", "resources")
    op.drop_constraint("uq_notes_vault_file_id", "notes")
