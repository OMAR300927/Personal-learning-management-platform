from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.models import (
    Task,
    TaskStatus,
    User,
)
from app.models.weekly_goal import WeeklyGoalScope, WeeklyGoalType
from app.services.learning_paths import create_learning_path, create_stage
from app.services.weekly_goals import (
    calculate_goal_progress,
    create_weekly_goal,
    update_weekly_goal,
)


async def test_weekly_goal_uniqueness_and_task_progress(
    db_session: AsyncSession,
) -> None:
    """Cap task progress and reject duplicate week/type/scope goals."""
    user = User(clerk_subject="user_a")
    db_session.add(user)
    await db_session.commit()

    path = await create_learning_path(db_session, "user_a", "Python")
    stage = await create_stage(db_session, path, "Basics")
    task = Task(
        learning_path_id=path.id,
        stage_id=stage.id,
        user_id="user_a",
        title="Variables",
        position=0,
        status=TaskStatus.COMPLETED,
    )
    db_session.add(task)
    await db_session.commit()

    goal = await create_weekly_goal(
        db_session,
        user,
        WeeklyGoalType.COMPLETED_TASKS,
        WeeklyGoalScope.LEARNING_PATH,
        path.id,
        1,
    )

    progress, percentage = await calculate_goal_progress(db_session, user, goal)
    assert progress == 1
    assert percentage == 100

    try:
        await create_weekly_goal(
            db_session,
            user,
            WeeklyGoalType.COMPLETED_TASKS,
            WeeklyGoalScope.LEARNING_PATH,
            path.id,
            2,
        )
        assert False, "Duplicate weekly goal should raise ApiError"

    except ApiError as error:
        assert error.status_code == 409


async def test_weekly_goal_edit_is_current_week_only(
    db_session: AsyncSession,
) -> None:
    """Reject editing a goal outside the current week."""
    user = User(clerk_subject="user_a")
    db_session.add(user)
    await db_session.commit()

    goal = await create_weekly_goal(
        db_session,
        user,
        WeeklyGoalType.LEARNING_HOURS,
        WeeklyGoalScope.OVERALL,
        None,
        5,
    )
    goal.week_start = goal.week_start - timedelta(days=7)
    await db_session.commit()

    try:
        await update_weekly_goal(db_session, user, goal, 10)
        assert False, "Past-week goal edit should raise ApiError"
        
    except ApiError as error:
        assert error.status_code == 409
