from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    GoalSnapshot,
    LearningTimeEntry,
    Task,
    TaskStatus,
    TaskStatusHistory,
    User,
)
from app.models.weekly_goal import WeeklyGoalScope, WeeklyGoalType
from app.services.learning_paths import create_learning_path, create_stage
from app.services.weekly_goals import create_weekly_goal
from app.worker.worker import finalize_weekly_goal_snapshots


async def test_worker_snapshot_is_idempotent_and_capped(
    db_session: AsyncSession,
) -> None:
    """Create exactly one immutable snapshot and cap progress at 100 percent."""
    user = User(clerk_subject="user_a", timezone="UTC")
    db_session.add(user)
    await db_session.commit()
    
    path = await create_learning_path(db_session, "user_a", "Python")
    goal = await create_weekly_goal(
        db_session,
        user,
        WeeklyGoalType.LEARNING_HOURS,
        WeeklyGoalScope.LEARNING_PATH,
        path.id,
        5,
    )
    goal.week_start = (datetime.now(timezone.utc).date() - timedelta(days=7))
    if goal.week_start.weekday() != 5:
        goal.week_start -= timedelta(days=(goal.week_start.weekday() - 5) % 7)

    await db_session.commit()

    db_session.add(
        LearningTimeEntry(
            user_id="user_a",
            learning_path_id=path.id,
            hours=8,
            occurred_at=datetime.combine(
                goal.week_start,
                datetime.min.time(),
                tzinfo=timezone.utc,
            ) + timedelta(hours=1),
            finalized=False,
        )
    )
    await db_session.commit()

    now = datetime.combine(
        goal.week_start + timedelta(days=7),
        datetime.min.time(),
        tzinfo=timezone.utc,
    )
    first = await finalize_weekly_goal_snapshots(db_session, now)
    second = await finalize_weekly_goal_snapshots(db_session, now)

    snapshots = (await db_session.scalars(select(GoalSnapshot))).all()
    assert first == 1
    assert second == 0
    assert len(snapshots) == 1
    assert snapshots[0].progress == 8
    assert snapshots[0].progress_percentage == 100


async def test_worker_reconstructs_task_status_at_boundary(
    db_session: AsyncSession,
) -> None:
    """Count completed status from timestamped history at the exact boundary."""
    user = User(clerk_subject="user_a", timezone="UTC")
    db_session.add(user)
    await db_session.commit()

    path = await create_learning_path(db_session, "user_a", "Python")
    stage_model = await create_stage(db_session, path, "Basics")
    task = Task(
        learning_path_id=path.id,
        stage_id=stage_model.id,
        user_id="user_a",
        title="Variables",
        position=0,
        status=TaskStatus.COMPLETED,
    )
    db_session.add(task)
    await db_session.flush()
    boundary = datetime(2026, 1, 2, tzinfo=timezone.utc)
    db_session.add(
        TaskStatusHistory(
            task_id=task.id,
            user_id="user_a",
            status=TaskStatus.IN_PROGRESS,
            changed_at=boundary - timedelta(hours=1),
        )
    )
    await db_session.commit()

    goal = await create_weekly_goal(
        db_session,
        user,
        WeeklyGoalType.COMPLETED_TASKS,
        WeeklyGoalScope.LEARNING_PATH,
        path.id,
        1,
    )
    goal.week_start = datetime(2025, 12, 27).date()
    await db_session.commit()

    await finalize_weekly_goal_snapshots(
        db_session,
        datetime(2026, 1, 3, tzinfo=timezone.utc),
    )
    snapshot = await db_session.scalar(select(GoalSnapshot))
    assert snapshot is not None
    assert snapshot.progress == 0
