"""Create fixed-week weekly goals.

Revision ID: 0007_weekly_goals
Revises: 0006_learning_time
Create Date: 2026-11-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0007_weekly_goals"
down_revision: str | None = "0006_learning_time"
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
    """Create weekly goals with database uniqueness per week/type/scope."""
    op.create_table(
        "weekly_goals",
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
            nullable=True,
        ),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("goal_type", goal_type, nullable=False),
        sa.Column("scope", goal_scope, nullable=False),
        sa.Column("scope_key", sa.String(length=64), nullable=False),
        sa.Column("target", sa.Float(), nullable=False),
        sa.UniqueConstraint(
            "user_id",
            "week_start",
            "goal_type",
            "scope_key",
            name="uq_weekly_goals_week_type_scope",
        ),
    )
    op.create_index("ix_weekly_goals_user_id", "weekly_goals", ["user_id"], unique=False)
    op.create_index(
        "ix_weekly_goals_learning_path_id",
        "weekly_goals",
        ["learning_path_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop weekly goals."""
    op.drop_index("ix_weekly_goals_learning_path_id", table_name="weekly_goals")
    op.drop_index("ix_weekly_goals_user_id", table_name="weekly_goals")
    op.drop_table("weekly_goals")
