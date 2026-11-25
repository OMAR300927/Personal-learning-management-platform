"""Create persistent application users.

Revision ID: 0002_create_users
Revises: 0001_initial
Create Date: 2026-11-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0002_create_users"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create a users table keyed by each verified Clerk subject."""
    op.create_table(
        "users",
        sa.Column("clerk_subject", sa.String(length=255), nullable=False),
        sa.Column(
            "timezone",
            sa.String(length=64),
            server_default="UTC",
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("clerk_subject"),
    )


def downgrade() -> None:
    """Drop the application users table."""
    op.drop_table("users")
