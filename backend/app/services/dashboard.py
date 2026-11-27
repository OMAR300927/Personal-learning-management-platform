from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.lib.week import validate_timezone
from app.models.goal_snapshot import GoalSnapshot
from app.models.learning_path import LearningPath
from app.models.learning_time import LearningTimeEntry
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.models.weekly_goal import WeeklyGoal
from app.schemas.dashboard import (
    DashboardData,
    DashboardGoalData,
    DashboardPathData,
)


def _parse_week(value: str | None, user: User) -> date:
    """Parse a selected Saturday or return the current Saturday."""
    if value is None:
        zone = validate_timezone(user.timezone)
        now = datetime.now(timezone.utc).astimezone(zone)
        local_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return (
            local_midnight - timedelta(days=(local_midnight.weekday() - 5) % 7)
        ).date()
    
    try:
        selected = date.fromisoformat(value)
        zone = validate_timezone(user.timezone)
        now = datetime.combine(selected, datetime.min.time(), tzinfo=zone)
        local_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        saturday = local_midnight - timedelta(
            days=(local_midnight.weekday() - 5) % 7
        )
        return saturday.date()
    
    except ValueError as error:
        raise ValueError("week must use YYYY-MM-DD") from error


def _parse_month(value: str | None, user: User) -> date:
    """Parse a selected month or return the current calendar month."""
    if value is None:
        zone = validate_timezone(user.timezone)
        now = datetime.now(timezone.utc).astimezone(zone)
        return date(now.year, now.month, 1)
    
    try:
        return date.fromisoformat(f"{value}-01")
    
    except ValueError as error:
        raise ValueError("month must use YYYY-MM") from error


async def _learning_hours_in_period(
    session: AsyncSession,
    user: User,
    start: datetime,
    end: datetime,
) -> float:
    """Sum owned learning-time entries between timezone-local boundaries."""
    entries = (
        await session.scalars(
            select(LearningTimeEntry).where(
                LearningTimeEntry.user_id == user.clerk_subject
            )
        )
    ).all()

    start_utc = start.astimezone(timezone.utc)
    end_utc = end.astimezone(timezone.utc)
    total = 0.0
    for entry in entries:
        occurred_at = entry.occurred_at
        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=timezone.utc)

        occurred_utc = occurred_at.astimezone(timezone.utc)
        if start_utc <= occurred_utc < end_utc:
            total += entry.hours

    return round(total, 2)


async def get_dashboard(
    session: AsyncSession,
    user: User,
    week: str | None = None,
    month: str | None = None,
) -> DashboardData:
    """Aggregate weekly, monthly, per-path, task, and goal dashboard metrics."""
    zone = validate_timezone(user.timezone)
    week_start_date = _parse_week(week, user)
    week_start = datetime.combine(
        week_start_date,
        datetime.min.time(),
        tzinfo=zone,
    )
    week_end = week_start + timedelta(days=7)

    month_start_date = _parse_month(month, user)
    if month_start_date.month == 12:
        month_end_date = date(month_start_date.year + 1, 1, 1)

    else:
        month_end_date = date(
            month_start_date.year,
            month_start_date.month + 1,
            1,
        )

    month_start = datetime.combine(
        month_start_date,
        datetime.min.time(),
        tzinfo=zone,
    )

    month_end = datetime.combine(
        month_end_date,
        datetime.min.time(),
        tzinfo=zone,
    )

    weekly_hours = await _learning_hours_in_period(
        session,
        user,
        week_start,
        week_end,
    )
    
    monthly_hours = await _learning_hours_in_period(
        session,
        user,
        month_start,
        month_end,
    )

    paths = (
        await session.scalars(
            select(LearningPath)
            .where(LearningPath.user_id == user.clerk_subject)
            .order_by(LearningPath.position, LearningPath.id)
        )
    ).all()
    path_responses: list[DashboardPathData] = []

    for path in paths:
        tasks = (
            await session.scalars(
                select(Task).where(
                    Task.user_id == user.clerk_subject,
                    Task.learning_path_id == path.id,
                )
            )
        ).all()

        if not tasks:
            completion = None

        else:
            completed = sum(task.status == TaskStatus.COMPLETED for task in tasks)
            completion = round(completed * 100 / len(tasks), 2)

        path_responses.append(
            {
                "id": path.id,
                "title": path.title,
                "completion_percentage": completion,
            }
        )

    all_tasks = (
        await session.scalars(
            select(Task).where(Task.user_id == user.clerk_subject)
        )
    ).all()

    completed_tasks = sum(
        task.status == TaskStatus.COMPLETED for task in all_tasks
    )
    
    incomplete_tasks = sum(
        task.status != TaskStatus.COMPLETED for task in all_tasks
    )

    goals = (
        await session.scalars(
            select(WeeklyGoal).where(
                WeeklyGoal.user_id == user.clerk_subject,
                WeeklyGoal.week_start == week_start_date,
            )
        )
    ).all()

    goal_responses: list[DashboardGoalData] = []
    now = datetime.now(timezone.utc)

    if week_end <= now.astimezone(zone):
        snapshots = (
            await session.scalars(
                select(GoalSnapshot).where(
                    GoalSnapshot.user_id == user.clerk_subject,
                    GoalSnapshot.week_start == week_start_date,
                )
            )
        ).all()

        snapshot_by_goal = {snapshot.goal_id: snapshot for snapshot in snapshots}
        for goal in goals:
            snapshot = snapshot_by_goal.get(goal.id)

            if snapshot is not None:
                progress = snapshot.progress
                percentage = snapshot.progress_percentage

            else:
                progress = 0.0
                percentage = 0.0

            goal_responses.append(
                {
                    "id": goal.id,
                    "goal_type": goal.goal_type.value,
                    "scope": goal.scope.value,
                    "target": goal.target,
                    "progress": progress,
                    "progress_percentage": percentage,
                }
            )
            
    else:
        for goal in goals:
            if goal.goal_type.value == "learning_hours":
                entries = (
                    await session.scalars(
                        select(LearningTimeEntry).where(
                            LearningTimeEntry.user_id == user.clerk_subject
                        )
                    )
                ).all()
                progress = 0.0

                for entry in entries:
                    if entry.occurred_at.tzinfo is None:
                        entry_at = entry.occurred_at.replace(tzinfo=timezone.utc)

                    else:
                        entry_at = entry.occurred_at

                    entry_utc = entry_at.astimezone(timezone.utc)
                    if week_start <= entry_utc.astimezone(zone) < week_end and (
                        goal.scope.value == "overall"
                        or entry.learning_path_id == goal.learning_path_id
                    ):
                        progress += entry.hours

            else:
                tasks_for_goal = (
                    await session.scalars(
                        select(Task).where(Task.user_id == user.clerk_subject)
                    )
                ).all()

                if goal.scope.value == "learning_path":
                    tasks_for_goal = [
                        task
                        for task in tasks_for_goal
                        if task.learning_path_id == goal.learning_path_id
                    ]

                progress = float(
                    sum(task.status == TaskStatus.COMPLETED for task in tasks_for_goal)
                )

            percentage = min(progress * 100 / goal.target, 100.0)
            goal_responses.append(
                {
                    "id": goal.id,
                    "goal_type": goal.goal_type.value,
                    "scope": goal.scope.value,
                    "target": goal.target,
                    "progress": progress,
                    "progress_percentage": round(percentage, 2),
                }
            )

    return {
        "week": {
            "start": week_start.date().isoformat(),
            "end": (week_end.date() - timedelta(days=1)).isoformat(),
            "total_learning_hours": weekly_hours,
        },
        "month": {
            "start": month_start.date().isoformat(),
            "end": (month_end.date() - timedelta(days=1)).isoformat(),
            "total_learning_hours": monthly_hours,
        },
        "paths": path_responses,
        "completed_tasks": completed_tasks,
        "incomplete_tasks": incomplete_tasks,
        "goals": goal_responses,
    }
