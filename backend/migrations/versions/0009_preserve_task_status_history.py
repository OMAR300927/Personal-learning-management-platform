"""Preserve task-status history after task deletion.

Revision ID: 0009_status_history
Revises: 0008_goal_snapshots
Create Date: 2026-11-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0009_status_history"
down_revision: str | None = "0008_goal_snapshots"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Retain task IDs and path scope independently of deleted task rows."""
    op.drop_index("ix_task_status_history_user_id", table_name="task_status_history")
    op.drop_index("ix_task_status_history_task_id", table_name="task_status_history")
    op.rename_table("task_status_history", "task_status_history_old")
    op.create_table(
        "task_status_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("learning_path_id", sa.Integer(), nullable=True),
        sa.Column(
            "user_id",
            sa.String(length=255),
            sa.ForeignKey("users.clerk_subject", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "Not Started",
                "In Progress",
                "Completed",
                name="task_status",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO task_status_history
                (id, task_id, learning_path_id, user_id, status, changed_at)
            SELECT h.id, h.task_id, t.learning_path_id, h.user_id, h.status, h.changed_at
            FROM task_status_history_old AS h
            LEFT JOIN tasks AS t ON t.id = h.task_id
            """
        )
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
    op.drop_table("task_status_history_old")


def downgrade() -> None:
    """Restore the prior task-status-history foreign-key shape."""
    op.drop_index("ix_task_status_history_user_id", table_name="task_status_history")
    op.drop_index("ix_task_status_history_task_id", table_name="task_status_history")
    op.rename_table("task_status_history", "task_status_history_new")
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
        sa.Column(
            "status",
            sa.Enum(
                "Not Started",
                "In Progress",
                "Completed",
                name="task_status",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO task_status_history
                (id, task_id, user_id, status, changed_at)
            SELECT id, task_id, user_id, status, changed_at
            FROM task_status_history_new
            WHERE EXISTS (SELECT 1 FROM tasks WHERE tasks.id = task_status_history_new.task_id)
            """
        )
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
    op.drop_table("task_status_history_new")
