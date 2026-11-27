from datetime import date, datetime, timezone

import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models import (
    GoalSnapshot,
    LearningPath,
    LearningTimeEntry,
    Link,
    Stage,
    Task,
    TaskStatus,
    TaskStatusHistory,
    User,
    WeeklyGoal,
    WeeklyGoalScope,
    WeeklyGoalType,
)
from app.models.deletion_record import DeletionRecord
from app.services.account_deletion import (
    ClerkAdminClient,
    ClerkDeletionError,
    delete_account,
    replay_deletion_ledger,
    retry_pending_clerk_deletions,
)


def test_settings_reject_shared_application_and_ledger_database() -> None:
    """Prevent accidentally configuring the ledger in the application database."""
    database_url = "sqlite+aiosqlite:///./data/shared.db"

    with pytest.raises(ValidationError):
        Settings(
            database_url=database_url,
            deletion_ledger_database_url=database_url,
        )


class SuccessfulClerkClient:
    """Provide a successful Clerk deletion response for service tests."""

    def __init__(self) -> None:
        """Initialize a request counter for idempotency assertions."""
        self.calls = 0
        self.deleted_subjects: list[str] = []

    async def delete_user(self, clerk_subject: str) -> None:
        """Record one simulated successful deletion request."""
        self.calls += 1
        self.deleted_subjects.append(clerk_subject)


class FailOnceClerkClient:
    """Simulate a transient Clerk failure followed by a successful retry."""

    def __init__(self) -> None:
        """Initialize the retry count."""
        self.calls = 0
        self.subjects: list[str] = []

    async def delete_user(self, clerk_subject: str) -> None:
        """Fail once with a sanitized code and succeed on the next call."""
        self.calls += 1
        self.subjects.append(clerk_subject)
        if self.calls == 1:
            raise ClerkDeletionError("provider_unavailable")


async def _seed_user_data(session: AsyncSession, subject: str) -> None:
    """Create representative live records and history for one account."""
    user = User(clerk_subject=subject)
    path = LearningPath(user_id=subject, title="Path", position=0)
    session.add_all([user, path])
    await session.flush()

    stage = Stage(
        learning_path_id=path.id,
        user_id=subject,
        title="Stage",
        position=0,
    )
    session.add(stage)
    await session.flush()

    task = Task(
        learning_path_id=path.id,
        stage_id=stage.id,
        user_id=subject,
        title="Task",
        position=0,
        status=TaskStatus.COMPLETED,
    )

    goal = WeeklyGoal(
        user_id=subject,
        week_start=date(2026, 11, 21),
        goal_type=WeeklyGoalType.LEARNING_HOURS,
        scope=WeeklyGoalScope.OVERALL,
        scope_key="overall",
        target=2,
    )
    session.add_all([task, goal])
    await session.flush()

    session.add_all(
        [
            Link(
                user_id=subject,
                target_type="path",
                target_id=path.id,
                title="Link",
                url="https://example.com",
            ),
            LearningTimeEntry(
                user_id=subject,
                learning_path_id=path.id,
                hours=1,
                occurred_at=datetime(2026, 11, 22, tzinfo=timezone.utc),
                finalized=False,
            ),
            TaskStatusHistory(
                task_id=task.id,
                learning_path_id=path.id,
                user_id=subject,
                status=TaskStatus.COMPLETED,
                changed_at=datetime(2026, 11, 22, tzinfo=timezone.utc),
            ),
            GoalSnapshot(
                goal_id=goal.id,
                user_id=subject,
                week_start=goal.week_start,
                goal_type=goal.goal_type,
                scope=goal.scope,
                target=goal.target,
                progress=1,
                progress_percentage=50,
            ),
        ],
    )
    await session.commit()


async def test_delete_account_removes_all_data_and_is_idempotent(
    db_session: AsyncSession,
    ledger_session: AsyncSession,
) -> None:
    """Delete all live/history records while retaining a durable tombstone."""
    await _seed_user_data(db_session, "user_a")
    client = SuccessfulClerkClient()
    settings = Settings()

    completed = await delete_account(
        db_session,
        ledger_session,
        "user_a",
        settings,
        client,
    )

    repeated = await delete_account(
        db_session,
        ledger_session,
        "user_a",
        settings,
        client,
    )

    assert completed is True
    assert repeated is True
    assert client.calls == 1
    assert client.deleted_subjects == ["user_a"]
    assert await ledger_session.get(DeletionRecord, "user_a") is not None
    
    for model in (
        GoalSnapshot,
        LearningPath,
        LearningTimeEntry,
        Link,
        Stage,
        Task,
        TaskStatusHistory,
        User,
        WeeklyGoal,
    ):
        count = await db_session.scalar(select(func.count()).select_from(model))
        assert count == 0


async def test_pending_clerk_deletion_retries_without_restoring_user_data(
    db_session: AsyncSession,
    ledger_session: AsyncSession,
) -> None:
    """Retry a transient Clerk failure while keeping the tombstone and purge."""
    await _seed_user_data(db_session, "user_a")
    client = FailOnceClerkClient()
    settings = Settings()

    completed = await delete_account(
        db_session,
        ledger_session,
        "user_a",
        settings,
        client,
    )
    record = await ledger_session.get(DeletionRecord, "user_a")

    assert completed is False
    assert record is not None
    assert record.last_error_code == "provider_unavailable"
    assert record.attempt_count == 1
    assert await db_session.get(User, "user_a") is None

    retried = await retry_pending_clerk_deletions(
        db_session,
        ledger_session,
        settings,
        client,
    )

    assert retried == 1
    assert client.calls == 2
    assert client.subjects == ["user_a", "user_a"]
    assert record.clerk_deleted_at is not None
    assert record.last_error_code is None
    assert await db_session.get(User, "user_a") is None


async def test_replay_deletion_ledger_removes_restored_records(
    db_session: AsyncSession,
    ledger_session: AsyncSession,
) -> None:
    """Reapply a deletion tombstone to application data restored from backup."""
    await _seed_user_data(db_session, "user_a")
    ledger_session.add(DeletionRecord(clerk_subject="user_a"))
    await ledger_session.commit()

    replayed = await replay_deletion_ledger(db_session, ledger_session)

    assert replayed == 1
    assert await db_session.get(User, "user_a") is None
    assert await db_session.scalar(select(func.count()).select_from(LearningPath)) == 0
    assert await ledger_session.get(DeletionRecord, "user_a") is not None


async def test_clerk_admin_client_treats_missing_identity_as_success() -> None:
    """Treat Clerk's not-found result as an idempotent completed deletion."""
    requests: list[httpx.Request] = []

    async def respond(request: httpx.Request) -> httpx.Response:
        """Capture the request and simulate an identity already being absent."""
        requests.append(request)
        return httpx.Response(404)

    client = ClerkAdminClient(
        Settings(clerk_secret_key="test-secret"),
        httpx.MockTransport(respond),
    )

    await client.delete_user("user/a")

    assert len(requests) == 1
    assert requests[0].url.raw_path == b"/v1/users/user%2Fa"
    assert requests[0].headers["Authorization"] == "Bearer test-secret"


async def test_clerk_admin_client_sanitizes_provider_failures() -> None:
    """Keep provider response bodies out of the persisted/logged error code."""

    async def respond(request: httpx.Request) -> httpx.Response:
        """Return a provider failure with content that must not be propagated."""
        assert request.url.path == "/v1/users/user_a"
        return httpx.Response(403, text="private provider response")

    client = ClerkAdminClient(
        Settings(clerk_secret_key="test-secret"),
        httpx.MockTransport(respond),
    )

    with pytest.raises(ClerkDeletionError) as error:
        await client.delete_user("user_a")

    assert error.value.code == "http_403"
    assert "private provider response" not in str(error.value)
