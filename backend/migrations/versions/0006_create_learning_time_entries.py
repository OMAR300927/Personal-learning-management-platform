"""Create path-level learning-time entries.

Revision ID: 0006_learning_time
Revises: 0005_links
Create Date: 2026-11-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0006_learning_time"
down_revision: str | None = "0005_links"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create learning-time entries with active-week finalization state."""
    op.create_table(
        "learning_time_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(length=255),
            sa.ForeignKey("users.clerk_subject", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "learning_path_id",
            sa.Integer(),
            sa.ForeignKey("learning_paths.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("hours", sa.Float(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finalized", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(
        "ix_learning_time_entries_user_id",
        "learning_time_entries",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_learning_time_entries_learning_path_id",
        "learning_time_entries",
        ["learning_path_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop learning-time entries."""
    op.drop_index(
        "ix_learning_time_entries_learning_path_id",
        table_name="learning_time_entries",
    )
    op.drop_index(
        "ix_learning_time_entries_user_id",
        table_name="learning_time_entries",
    )
    op.drop_table("learning_time_entries")
