from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.deletion_ledger_base import DeletionLedgerBase


class DeletionRecord(DeletionLedgerBase):
    """Retain an account-deletion tombstone and Clerk retry state."""

    __tablename__ = "deletion_records"

    clerk_subject: Mapped[str] = mapped_column(String(255), primary_key=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    clerk_deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_attempted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    last_error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
