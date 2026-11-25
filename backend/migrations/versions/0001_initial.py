"""Create the initial migration baseline.

Revision ID: 0001_initial
Revises:
Create Date: 2026-11-24
"""

from collections.abc import Sequence


revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply the empty baseline migration before product tables are added."""
    pass


def downgrade() -> None:
    """Revert the empty baseline migration without changing application data."""
    pass
