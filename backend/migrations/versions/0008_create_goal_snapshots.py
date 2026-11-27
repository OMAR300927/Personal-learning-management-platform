"""Create immutable weekly-goal snapshots.

Revision ID: 0008_goal_snapshots
Revises: 0007_weekly_goals
Create Date: 2026-11-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0008_goal_snapshots"
down_revision: str | None = "0007_weekly_goals"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

goal_type = sa.Enum(
    "learning_hours",
    "completed_tasks",
    name="weekly_goal_type",
    native_enum=False,
)
goal_scope = sa.Enum(
    "overall",
    "learning_path",
    name="weekly_goal_scope",
    native_enum=False,
)


def upgrade() -> None:
    """Create immutable snapshot records with one snapshot per goal/week."""
    op.create_table(
        "goal_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "goal_id",
            sa.Integer(),
            sa.ForeignKey("weekly_goals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(length=255),
            sa.ForeignKey("users.clerk_subject", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "learning_path_id",
            sa.Integer(),
            sa.ForeignKey("learning_paths.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("goal_type", goal_type, nullable=False),
        sa.Column("scope", goal_scope, nullable=False),
        sa.Column("target", sa.Float(), nullable=False),
        sa.Column("progress", sa.Float(), nullable=False),
        sa.Column("progress_percentage", sa.Float(), nullable=False),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "goal_id",
            "week_start",
            name="uq_goal_snapshots_goal_week",
        ),
    )
    op.create_index("ix_goal_snapshots_goal_id", "goal_snapshots", ["goal_id"], unique=False)
    op.create_index("ix_goal_snapshots_user_id", "goal_snapshots", ["user_id"], unique=False)


def downgrade() -> None:
    """Drop goal snapshots."""
    op.drop_index("ix_goal_snapshots_user_id", table_name="goal_snapshots")
    op.drop_index("ix_goal_snapshots_goal_id", table_name="goal_snapshots")
    op.drop_table("goal_snapshots")
