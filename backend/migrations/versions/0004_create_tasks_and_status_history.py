"""Create tasks and timestamped task-status history.

Revision ID: 0004_tasks
Revises: 0003_learning_paths
Create Date: 2026-11-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0004_tasks"
down_revision: str | None = "0003_learning_paths"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

task_status = sa.Enum(
    "Not Started",
    "In Progress",
    "Completed",
    name="task_status",
    native_enum=False,
)


def upgrade() -> None:
    """Create tasks and immutable timestamped status-history records."""
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "learning_path_id",
            sa.Integer(),
            sa.ForeignKey("learning_paths.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "stage_id",
            sa.Integer(),
            sa.ForeignKey("stages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(length=255),
            sa.ForeignKey("users.clerk_subject", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            task_status,
            nullable=False,
            server_default="Not Started",
        ),
        sa.UniqueConstraint("stage_id", "title", name="uq_tasks_stage_title"),
    )
    op.create_index("ix_tasks_learning_path_id", "tasks", ["learning_path_id"], unique=False)
    op.create_index("ix_tasks_stage_id", "tasks", ["stage_id"], unique=False)
    op.create_index("ix_tasks_user_id", "tasks", ["user_id"], unique=False)

    op.create_table(
        "task_status_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "task_id",
            sa.Integer(),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(length=255),
            sa.ForeignKey("users.clerk_subject", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", task_status, nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_task_status_history_task_id",
        "task_status_history",
        ["task_id"],
        unique=False,
    )
    op.create_index(
        "ix_task_status_history_user_id",
        "task_status_history",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop task-status history before tasks."""
    op.drop_index("ix_task_status_history_user_id", table_name="task_status_history")
    op.drop_index("ix_task_status_history_task_id", table_name="task_status_history")
    op.drop_table("task_status_history")
    op.drop_index("ix_tasks_user_id", table_name="tasks")
    op.drop_index("ix_tasks_stage_id", table_name="tasks")
    op.drop_index("ix_tasks_learning_path_id", table_name="tasks")
    op.drop_table("tasks")
