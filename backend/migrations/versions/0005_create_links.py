"""Create links attached to learning paths, stages, and tasks.

Revision ID: 0005_links
Revises: 0004_tasks
Create Date: 2026-11-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0005_links"
down_revision: str | None = "0004_tasks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create owner-scoped links with polymorphic target references."""
    op.create_table(
        "links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(length=255),
            sa.ForeignKey("users.clerk_subject", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("target_type", sa.String(length=16), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.UniqueConstraint(
            "user_id",
            "target_type",
            "target_id",
            "title",
            name="uq_links_target_title",
        ),
    )
    op.create_index("ix_links_user_id", "links", ["user_id"], unique=False)
    op.create_index(
        "ix_links_target",
        "links",
        ["target_type", "target_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop polymorphic links."""
    op.drop_index("ix_links_target", table_name="links")
    op.drop_index("ix_links_user_id", table_name="links")
    op.drop_table("links")
