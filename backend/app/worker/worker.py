from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.lib.week import current_saturday_friday_week, saturday_friday_week
from app.models.goal_snapshot import GoalSnapshot
from app.models.learning_time import LearningTimeEntry
from app.models.task import Task, TaskStatus, TaskStatusHistory
from app.models.user import User
from app.models.weekly_goal import WeeklyGoal, WeeklyGoalScope, WeeklyGoalType


def _utc_datetime(value: datetime) -> datetime:
    """Normalize a datetime to UTC for boundary comparisons."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


async def _snapshot_task_progress(
    session: AsyncSession,
    goal: WeeklyGoal,
    boundary_utc: datetime,
) -> float:
    """Reconstruct completed-task count as of the exact week boundary."""
    statement = select(Task).where(Task.user_id == goal.user_id)
    if goal.scope == WeeklyGoalScope.LEARNING_PATH:
        statement = statement.where(Task.learning_path_id == goal.learning_path_id)

    tasks = (await session.scalars(statement)).all()

    completed = 0
    for task in tasks:
        histories = (
            await session.scalars(
                select(TaskStatusHistory)
                .where(TaskStatusHistory.task_id == task.id)
                .order_by(TaskStatusHistory.changed_at.desc())
            )
        ).all()

        status = task.status
        for history in histories:
            if _utc_datetime(history.changed_at) <= boundary_utc:
                status = history.status
                break

        if status == TaskStatus.COMPLETED:
            completed += 1

    history_statement = (
        select(TaskStatusHistory)
        .where(
            TaskStatusHistory.user_id == goal.user_id,
            TaskStatusHistory.learning_path_id == goal.learning_path_id,
        )
        .order_by(TaskStatusHistory.task_id, TaskStatusHistory.changed_at.desc())
    )

    if goal.scope == WeeklyGoalScope.OVERALL:
        history_statement = (
            select(TaskStatusHistory)
            .where(
                TaskStatusHistory.user_id == goal.user_id,
            )
            .order_by(TaskStatusHistory.task_id, TaskStatusHistory.changed_at.desc())
        )

    histories = (await session.scalars(history_statement)).all()
    live_task_ids = {task.id for task in tasks}
    latest_deleted_status: dict[int, TaskStatus] = {}
    for history in histories:
        if history.task_id in live_task_ids:
            continue

        if history.task_id in latest_deleted_status:
            continue

        if _utc_datetime(history.changed_at) <= boundary_utc:
            latest_deleted_status[history.task_id] = history.status

    completed += sum(
        status == TaskStatus.COMPLETED
        for status in latest_deleted_status.values()
    )
    return float(completed)


async def _snapshot_learning_hours(
    session: AsyncSession,
    user: User,
    goal: WeeklyGoal,
    week_start: datetime,
    week_end: datetime,
) -> float:
    """Sum learning-time entries whose occurrence falls inside the snapshot week."""
    statement = select(LearningTimeEntry).where(
        LearningTimeEntry.user_id == user.clerk_subject
    )
    if goal.scope == WeeklyGoalScope.LEARNING_PATH:
        statement = statement.where(
            LearningTimeEntry.learning_path_id == goal.learning_path_id
        )

    entries = (await session.scalars(statement)).all()

    progress = 0.0
    for entry in entries:
        occurred_at = _utc_datetime(entry.occurred_at)
        if week_start <= occurred_at < week_end:
            progress += entry.hours

    return progress


async def finalize_weekly_goal_snapshots(
    session: AsyncSession,
    now: datetime | None = None,
) -> int:
    """Finalize ended weekly goals once, without modifying existing snapshots."""
    moment = now or datetime.now(timezone.utc)
    created = 0
    users = (await session.scalars(select(User))).all()

    for user in users:
        current_start, _ = current_saturday_friday_week(user.timezone, moment)
        zone = ZoneInfo(user.timezone)
        current_start = current_start.astimezone(zone)
        goals = (
            await session.scalars(
                select(WeeklyGoal).where(
                    WeeklyGoal.user_id == user.clerk_subject,
                    WeeklyGoal.week_start < current_start.date(),
                )
            )
        ).all()

        for goal in goals:
            snapshot = await session.scalar(
                select(GoalSnapshot).where(
                    GoalSnapshot.goal_id == goal.id,
                    GoalSnapshot.week_start == goal.week_start,
                )
            )

            if snapshot is not None:
                continue

            week_start_local = datetime.combine(
                goal.week_start,
                datetime.min.time(),
                tzinfo=zone,
            )
            week_end_local = week_start_local + timedelta(days=7)
            week_start_utc = week_start_local.astimezone(timezone.utc)
            week_end_utc = week_end_local.astimezone(timezone.utc)

            if goal.goal_type == WeeklyGoalType.LEARNING_HOURS:
                progress = await _snapshot_learning_hours(
                    session,
                    user,
                    goal,
                    week_start_utc,
                    week_end_utc,
                )

            else:
                progress = await _snapshot_task_progress(
                    session,
                    goal,
                    week_end_utc,
                )

            percentage = min(progress * 100 / goal.target, 100.0)
            snapshot = GoalSnapshot(
                goal_id=goal.id,
                user_id=user.clerk_subject,
                learning_path_id=goal.learning_path_id,
                week_start=goal.week_start,
                goal_type=goal.goal_type,
                scope=goal.scope,
                target=goal.target,
                progress=progress,
                progress_percentage=round(percentage, 2),
            )
            session.add(snapshot)

            try:
                await session.commit()
                created += 1

            except IntegrityError:
                await session.rollback()

        entries = (
            await session.scalars(
                select(LearningTimeEntry).where(
                    LearningTimeEntry.user_id == user.clerk_subject,
                    LearningTimeEntry.finalized.is_(False),
                )
            )
        ).all()

        for entry in entries:
            _, week_end = saturday_friday_week(
                entry.occurred_at,
                user.timezone,
            )

            if moment.astimezone(zone) >= week_end:
                entry.finalized = True

        await session.commit()

    return created


async def retry_weekly_goal_snapshot_worker(
    session: AsyncSession,
    now: datetime | None = None,
    attempts: int = 2,
) -> int:
    """Retry transient worker failures and keep writes idempotent."""
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            return await finalize_weekly_goal_snapshots(session, now)
        
        except IntegrityError as error:
            await session.rollback()
            last_error = error

    if last_error is not None:
        raise last_error
    
    return 0


async def run_scheduled_worker() -> int:
    """Run snapshot processing and retry pending Clerk account deletions."""
    from app.core.config import get_settings
    from app.db.deletion_ledger import DeletionLedgerSessionFactory
    from app.db.session import SessionFactory
    from app.services.account_deletion import retry_pending_clerk_deletions

    async with SessionFactory() as session:
        snapshots_created = await retry_weekly_goal_snapshot_worker(session)

    async with (
        SessionFactory() as app_session,
        DeletionLedgerSessionFactory() as ledger_session,
    ):
        await retry_pending_clerk_deletions(
            app_session,
            ledger_session,
            get_settings(),
        )

    return snapshots_created


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_scheduled_worker())
