"""Create persistent deletion-ledger records.

Revision ID: 0001_deletion_records
Revises:
Create Date: 2026-11-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0001_deletion_records"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the independent tombstone and Clerk retry-state table."""
    op.create_table(
        "deletion_records",
        sa.Column("clerk_subject", sa.String(length=255), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("clerk_deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "attempt_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column("last_error_code", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("clerk_subject"),
    )


def downgrade() -> None:
    """Drop deletion-ledger data only when explicitly downgrading its schema."""
    op.drop_table("deletion_records")
