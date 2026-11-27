from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.models import TaskStatus, TaskStatusHistory, User
from app.services.learning_paths import create_learning_path, create_stage
from app.services.tasks import (
    calculate_path_completion,
    change_task_status,
    create_task,
    update_task,
)


async def test_task_status_history_and_path_completion(db_session: AsyncSession) -> None:
    """Track status changes and calculate completed-task percentage."""
    db_session.add(User(clerk_subject="user_a"))
    await db_session.commit()

    path = await create_learning_path(db_session, "user_a", "Python")
    stage = await create_stage(db_session, path, "Basics")
    first = await create_task(db_session, stage, "Variables")
    second = await create_task(db_session, stage, "Functions")

    assert first.status == TaskStatus.NOT_STARTED
    history = (await db_session.scalars(select(TaskStatusHistory))).all()
    assert len(history) == 2

    await change_task_status(db_session, first, TaskStatus.COMPLETED)
    await change_task_status(db_session, second, TaskStatus.IN_PROGRESS)
    assert await calculate_path_completion(db_session, "user_a", path.id) == 50.0

    await change_task_status(db_session, first, TaskStatus.NOT_STARTED)
    assert await calculate_path_completion(db_session, "user_a", path.id) == 0.0
    assert len((await db_session.scalars(select(TaskStatusHistory))).all()) == 5

    await update_task(db_session, second, "Function Basics")
    assert second.title == "Function Basics"


async def test_task_title_is_unique_within_stage(db_session: AsyncSession) -> None:
    """Reject duplicate task titles among siblings."""
    db_session.add(User(clerk_subject="user_a"))
    await db_session.commit()
    path = await create_learning_path(db_session, "user_a", "Python")
    stage = await create_stage(db_session, path, "Basics")
    await create_task(db_session, stage, "Variables")

    try:
        await create_task(db_session, stage, "Variables")
        assert False, "Duplicate task title should raise ApiError"

    except ApiError as error:
        assert error.status_code == 409


async def test_empty_path_completion_is_not_applicable(db_session: AsyncSession) -> None:
    """Return N/A for a path that has no tasks."""
    db_session.add(User(clerk_subject="user_a"))
    await db_session.commit()
    path = await create_learning_path(db_session, "user_a", "Python")

    assert await calculate_path_completion(db_session, "user_a", path.id) is None
