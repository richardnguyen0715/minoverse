"""Add unique constraint on resource_contents.resource_id.

Revises: 004
"""
from collections.abc import Sequence

from alembic import op

revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Keep only the latest row per resource_id before adding the constraint
    op.execute(
        """
        DELETE FROM resource_contents rc1
        USING resource_contents rc2
        WHERE rc1.resource_id = rc2.resource_id
          AND rc1.created_at < rc2.created_at
        """
    )
    op.create_unique_constraint(
        "uq_resource_contents_resource_id",
        "resource_contents",
        ["resource_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_resource_contents_resource_id",
        "resource_contents",
        type_="unique",
    )
