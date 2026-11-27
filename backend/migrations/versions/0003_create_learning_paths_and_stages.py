"""Create learning paths and stages.

Revision ID: 0003_learning_paths
Revises: 0002_create_users
Create Date: 2026-11-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0003_learning_paths"
down_revision: str | None = "0002_create_users"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create owner-scoped learning paths and path-owned stages."""
    op.create_table(
        "learning_paths",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(length=255),
            sa.ForeignKey("users.clerk_subject", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.UniqueConstraint(
            "user_id",
            "title",
            name="uq_learning_paths_owner_title",
        ),
    )
    op.create_index(
        "ix_learning_paths_user_id",
        "learning_paths",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "stages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "learning_path_id",
            sa.Integer(),
            sa.ForeignKey("learning_paths.id", ondelete="CASCADE"),
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
        sa.UniqueConstraint(
            "learning_path_id",
            "title",
            name="uq_stages_path_title",
        ),
    )
    op.create_index("ix_stages_learning_path_id", "stages", ["learning_path_id"], unique=False)
    op.create_index("ix_stages_user_id", "stages", ["user_id"], unique=False)


def downgrade() -> None:
    """Drop stages before learning paths."""
    op.drop_index("ix_stages_user_id", table_name="stages")
    op.drop_index("ix_stages_learning_path_id", table_name="stages")
    op.drop_table("stages")
    op.drop_index("ix_learning_paths_user_id", table_name="learning_paths")
    op.drop_table("learning_paths")
