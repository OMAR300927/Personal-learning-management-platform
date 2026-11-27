from datetime import datetime
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.lib.week import current_saturday_friday_week, saturday_friday_week
from app.models.learning_time import LearningTimeEntry
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.models.weekly_goal import (
    WeeklyGoal,
    WeeklyGoalScope,
    WeeklyGoalType,
)


def _current_week_start(user: User, now: datetime | None = None) -> object:
    """Return the current Saturday week start as a date."""
    start, _ = current_saturday_friday_week(user.timezone, now)
    return start.date()


def _validate_goal(
    goal_type: WeeklyGoalType,
    scope: WeeklyGoalScope,
    learning_path_id: int | None,
    target: float,
) -> str:
    """Validate scope/target combinations and return the scope key."""
    if scope == WeeklyGoalScope.OVERALL:
        if learning_path_id is not None:
            raise ApiError(
                "validation_error",
                "Overall goals cannot specify a learning path",
                422,
            )
        scope_key = "overall"

    else:
        if learning_path_id is None:
            raise ApiError(
                "validation_error",
                "Path-specific goals require a learning path",
                422,
            )
        scope_key = f"path:{learning_path_id}"

    if goal_type == WeeklyGoalType.COMPLETED_TASKS:
        if not target.is_integer():
            raise ApiError(
                "validation_error",
                "Completed-task goals must use a whole-number target",
                422,
            )
    return scope_key


async def calculate_goal_progress(
    session: AsyncSession,
    user: User,
    goal: WeeklyGoal,
) -> tuple[float, float]:
    """Calculate capped active-week progress for a goal."""
    if goal.goal_type == WeeklyGoalType.LEARNING_HOURS:
        statement = (
            select(LearningTimeEntry).where(
                LearningTimeEntry.user_id == user.clerk_subject
            )
        )
        
        if goal.scope == WeeklyGoalScope.LEARNING_PATH:
            statement = statement.where(
                LearningTimeEntry.learning_path_id == goal.learning_path_id
            )
        entries = (
            await session.scalars(
                statement
            )
        ).all()

        progress = 0.0
        for entry in entries:
            entry_start, _ = saturday_friday_week(entry.occurred_at, user.timezone)

            if entry_start.date() == goal.week_start:
                progress += entry.hours

    else:
        statement = select(Task).where(Task.user_id == user.clerk_subject)
        if goal.scope == WeeklyGoalScope.LEARNING_PATH:
            statement = statement.where(Task.learning_path_id == goal.learning_path_id)

        tasks = (await session.scalars(statement)).all()
        progress = float(
            sum(task.status == TaskStatus.COMPLETED for task in tasks)
        )

    percentage = min(progress * 100 / goal.target, 100.0)
    return progress, round(percentage, 2)


async def list_weekly_goals(
    session: AsyncSession,
    user: User,
) -> Sequence[WeeklyGoal]:
    """List the user's goals for the current week."""
    week_start = _current_week_start(user)
    statement = (
        select(WeeklyGoal)
        .where(
            WeeklyGoal.user_id == user.clerk_subject,
            WeeklyGoal.week_start == week_start,
        )
        .order_by(WeeklyGoal.id)
    )
    return (await session.scalars(statement)).all()


async def create_weekly_goal(
    session: AsyncSession,
    user: User,
    goal_type: WeeklyGoalType,
    scope: WeeklyGoalScope,
    learning_path_id: int | None,
    target: float,
) -> WeeklyGoal:
    """Create a goal only for the current user-local week."""
    if target <= 0:
        raise ApiError("validation_error", "Target must be greater than zero", 422)
    
    scope_key = _validate_goal(goal_type, scope, learning_path_id, target)
    week_start = _current_week_start(user)

    existing = await session.scalar(
        select(WeeklyGoal.id).where(
            WeeklyGoal.user_id == user.clerk_subject,
            WeeklyGoal.week_start == week_start,
            WeeklyGoal.goal_type == goal_type,
            WeeklyGoal.scope_key == scope_key,
        )
    )

    if existing is not None:
        raise ApiError(
            "conflict",
            "A goal already exists for this week, type, and scope",
            409,
        )

    goal = WeeklyGoal(
        user_id=user.clerk_subject,
        learning_path_id=learning_path_id,
        week_start=week_start,
        goal_type=goal_type,
        scope=scope,
        scope_key=scope_key,
        target=target,
    )
    session.add(goal)

    try:
        await session.commit()

    except IntegrityError as error:
        await session.rollback()
        raise ApiError(
            "conflict",
            "A goal already exists for this week, type, and scope",
            409,
        ) from error
    
    await session.refresh(goal)
    return goal


async def get_weekly_goal(
    session: AsyncSession,
    user_id: str,
    goal_id: int,
) -> WeeklyGoal | None:
    """Fetch one owned weekly goal."""
    statement = select(WeeklyGoal).where(
        WeeklyGoal.id == goal_id,
        WeeklyGoal.user_id == user_id,
    )
    return await session.scalar(statement)


async def update_weekly_goal(
    session: AsyncSession,
    user: User,
    goal: WeeklyGoal,
    target: float,
) -> WeeklyGoal:
    """Edit a goal only while it belongs to the current week."""
    if target <= 0:
        raise ApiError("validation_error", "Target must be greater than zero", 422)
    
    if goal.week_start != _current_week_start(user):
        raise ApiError(
            "conflict",
            "Goals can only be edited for the current week",
            409,
        )
    
    if (
        goal.goal_type == WeeklyGoalType.COMPLETED_TASKS
        and not float(target).is_integer()
    ):
        raise ApiError(
            "validation_error",
            "Completed-task goals must use a whole-number target",
            422,
        )

    goal.target = target
    await session.commit()
    await session.refresh(goal)
    return goal
