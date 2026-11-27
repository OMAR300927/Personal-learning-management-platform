import logging
from datetime import datetime, timezone
from typing import Protocol
from urllib.parse import quote

import httpx
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models import (
    GoalSnapshot,
    LearningPath,
    LearningTimeEntry,
    Link,
    Stage,
    Task,
    TaskStatusHistory,
    User,
    WeeklyGoal,
)
from app.models.deletion_record import DeletionRecord


logger = logging.getLogger(__name__)


class ClerkDeletionError(Exception):
    """Represent a safe-to-log Clerk deletion failure code."""

    def __init__(self, code: str) -> None:
        """Store a provider failure code without retaining response content."""
        self.code = code


class ClerkUserDeletionClient(Protocol):
    """Define the Clerk identity deletion operation used by the workflow."""

    async def delete_user(self, clerk_subject: str, /) -> None:
        """Delete one Clerk identity or raise a sanitized provider error."""


class ClerkAdminClient:
    """Call Clerk's server-side user deletion endpoint."""

    def __init__(
        self,
        settings: Settings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        """Configure the client with the Clerk server secret and optional transport."""
        self._secret_key = settings.clerk_secret_key
        self._transport = transport

    async def delete_user(self, clerk_subject: str) -> None:
        """Delete the Clerk identity, treating an already-absent user as success."""
        if not self._secret_key:
            raise ClerkDeletionError("secret_not_configured")

        url_subject = quote(clerk_subject, safe="")
        try:
            async with httpx.AsyncClient(
                timeout=10.0,
                transport=self._transport,
            ) as client:
                response = await client.delete(
                    f"https://api.clerk.com/v1/users/{url_subject}",
                    headers={"Authorization": f"Bearer {self._secret_key}"},
                )

        except httpx.HTTPError as error:
            raise ClerkDeletionError("transport_error") from error

        if response.status_code == 404 or response.is_success:
            return

        raise ClerkDeletionError(f"http_{response.status_code}")


async def is_subject_deleted(
    ledger_session: AsyncSession,
    clerk_subject: str,
) -> bool:
    """Check the independent ledger before resolving an application user."""
    return await ledger_session.get(DeletionRecord, clerk_subject) is not None


async def _ensure_deletion_record(
    ledger_session: AsyncSession,
    clerk_subject: str,
) -> DeletionRecord:
    """Durably create or retrieve the account's idempotent deletion tombstone."""
    record = await ledger_session.get(DeletionRecord, clerk_subject)
    if record is not None:
        return record

    record = DeletionRecord(clerk_subject=clerk_subject)
    ledger_session.add(record)
    try:
        await ledger_session.commit()
        
    except IntegrityError:
        await ledger_session.rollback()
        record = await ledger_session.get(DeletionRecord, clerk_subject)
        if record is None:
            raise

    return record


async def delete_live_user_data(
    app_session: AsyncSession,
    clerk_subject: str,
) -> None:
    """Delete all product data and the local identity for one Clerk subject."""
    deletions = (
        (GoalSnapshot, GoalSnapshot.user_id),
        (TaskStatusHistory, TaskStatusHistory.user_id),
        (Link, Link.user_id),
        (LearningTimeEntry, LearningTimeEntry.user_id),
        (Task, Task.user_id),
        (WeeklyGoal, WeeklyGoal.user_id),
        (Stage, Stage.user_id),
        (LearningPath, LearningPath.user_id),
        (User, User.clerk_subject),
    )
    for model, owner_column in deletions:
        await app_session.execute(
            delete(model).where(owner_column == clerk_subject),
        )

    await app_session.commit()


async def _attempt_clerk_deletion(
    ledger_session: AsyncSession,
    record: DeletionRecord,
    client: ClerkUserDeletionClient,
) -> None:
    """Attempt Clerk deletion and persist retry state without logging secrets."""
    if record.clerk_deleted_at is not None:
        return

    record.attempt_count += 1
    record.last_attempted_at = datetime.now(timezone.utc)
    await ledger_session.commit()

    try:
        await client.delete_user(record.clerk_subject)

    except ClerkDeletionError as error:
        record.last_error_code = error.code
        await ledger_session.commit()
        logger.error(
            "account_deletion_clerk_retry_required error_code=%s",
            error.code,
        )
        return

    record.clerk_deleted_at = datetime.now(timezone.utc)
    record.last_error_code = None
    await ledger_session.commit()


async def delete_account(
    app_session: AsyncSession,
    ledger_session: AsyncSession,
    clerk_subject: str,
    settings: Settings,
    clerk_client: ClerkUserDeletionClient | None = None,
) -> bool:
    """Block access, remove application data, and request Clerk deletion."""
    record = await _ensure_deletion_record(ledger_session, clerk_subject)
    await delete_live_user_data(app_session, clerk_subject)
    await _attempt_clerk_deletion(
        ledger_session,
        record,
        clerk_client or ClerkAdminClient(settings),
    )
    return record.clerk_deleted_at is not None


async def replay_deletion_ledger(
    app_session: AsyncSession,
    ledger_session: AsyncSession,
) -> int:
    """Re-delete every ledgered account before restored data can be served."""
    try:
        records = (
            await ledger_session.scalars(
                select(DeletionRecord).order_by(DeletionRecord.requested_at),
            )
        ).all()

        for record in records:
            await delete_live_user_data(app_session, record.clerk_subject)

    except SQLAlchemyError:
        logger.error("account_deletion_restore_replay_failure")
        raise

    return len(records)


async def retry_pending_clerk_deletions(
    app_session: AsyncSession,
    ledger_session: AsyncSession,
    settings: Settings,
    clerk_client: ClerkUserDeletionClient | None = None,
    batch_size: int = 100,
) -> int:
    """Retry pending Clerk deletions after reapplying local-data removal."""
    records = (
        await ledger_session.scalars(
            select(DeletionRecord)
            .where(DeletionRecord.clerk_deleted_at.is_(None))
            .order_by(DeletionRecord.requested_at)
            .limit(batch_size),
        )
    ).all()
    client = clerk_client or ClerkAdminClient(settings)

    for record in records:
        try:
            await delete_live_user_data(app_session, record.clerk_subject)
            await _attempt_clerk_deletion(ledger_session, record, client)
            
        except SQLAlchemyError:
            logger.error("account_deletion_database_failure")
            raise

    return len(records)
