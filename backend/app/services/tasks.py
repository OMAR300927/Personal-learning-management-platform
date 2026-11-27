from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.models.stage import Stage
from app.models.task import Task, TaskStatus, TaskStatusHistory
from app.services.links import delete_target_links


async def list_tasks(session: AsyncSession, stage: Stage) -> Sequence[Task]:
    """List an owned stage's tasks in their configured order."""
    statement = (
        select(Task)
        .where(Task.stage_id == stage.id, Task.user_id == stage.user_id)
        .order_by(Task.position, Task.id)
    )
    return (await session.scalars(statement)).all()


async def create_task(
    session: AsyncSession,
    stage: Stage,
    title: str,
) -> Task:
    """Create a task, timestamp its initial status, and place it last."""
    existing = await session.scalar(
        select(Task.id).where(Task.stage_id == stage.id, Task.title == title)
    )
    if existing is not None:
        raise ApiError("conflict", "A task with this title already exists", 409)

    position = await session.scalar(
        select(Task.position)
        .where(Task.stage_id == stage.id)
        .order_by(Task.position.desc())
        .limit(1)
    )

    task = Task(
        learning_path_id=stage.learning_path_id,
        stage_id=stage.id,
        user_id=stage.user_id,
        title=title,
        position=(position + 1) if position is not None else 0,
        status=TaskStatus.NOT_STARTED,
    )

    session.add(task)
    await session.flush()
    session.add(
        TaskStatusHistory(
            task_id=task.id,
            user_id=stage.user_id,
            learning_path_id=task.learning_path_id,
            status=TaskStatus.NOT_STARTED,
        )
    )
    await session.commit()
    await session.refresh(task)
    return task


async def get_task(
    session: AsyncSession,
    user_id: str,
    task_id: int,
) -> Task | None:
    """Fetch one owned task."""
    statement = select(Task).where(Task.id == task_id, Task.user_id == user_id)
    return await session.scalar(statement)


async def update_task(
    session: AsyncSession,
    task: Task,
    title: str,
) -> Task:
    """Rename a task after checking sibling-title uniqueness."""
    existing = await session.scalar(
        select(Task.id).where(
            Task.stage_id == task.stage_id,
            Task.title == title,
            Task.id != task.id,
        )
    )
    if existing is not None:
        raise ApiError("conflict", "A task with this title already exists", 409)

    task.title = title
    await session.commit()
    await session.refresh(task)
    return task


async def change_task_status(
    session: AsyncSession,
    task: Task,
    status: TaskStatus,
) -> Task:
    """Change a task status and append a timestamped history record."""
    if task.status != status:
        task.status = status
        session.add(
            TaskStatusHistory(
                task_id=task.id,
                user_id=task.user_id,
                learning_path_id=task.learning_path_id,
                status=status,
            )
        )

    await session.commit()
    await session.refresh(task)
    return task


async def reorder_task(
    session: AsyncSession,
    task: Task,
    position: int,
) -> Task:
    """Move a task within its stage and normalize sibling positions."""
    if position < 0:
        raise ApiError("validation_error", "Position must be zero or greater", 422)

    siblings = (
        await session.scalars(
            select(Task)
            .where(Task.stage_id == task.stage_id)
            .order_by(Task.position, Task.id)
        )
    ).all()

    siblings = [item for item in siblings if item.id != task.id]
    position = min(position, len(siblings))
    siblings.insert(position, task)

    for index, item in enumerate(siblings):
        item.position = index

    await session.commit()
    await session.refresh(task)
    return task


async def delete_task(session: AsyncSession, task: Task) -> None:
    """Delete a task and normalize remaining siblings in its stage."""
    stage_id = task.stage_id
    await delete_target_links(session, "task", task.id)
    await session.delete(task)
    await session.flush()

    siblings = (
        await session.scalars(
            select(Task)
            .where(Task.stage_id == stage_id)
            .order_by(Task.position, Task.id)
        )
    ).all()

    for index, sibling in enumerate(siblings):
        sibling.position = index

    await session.commit()


async def calculate_path_completion(
    session: AsyncSession,
    user_id: str,
    learning_path_id: int,
) -> float | None:
    """Calculate completed-task percentage, or N/A for paths with no tasks."""
    statement = select(Task.status).where(
        Task.user_id == user_id,
        Task.learning_path_id == learning_path_id,
    )
    
    statuses = (await session.scalars(statement)).all()
    if not statuses:
        return None

    completed = sum(status == TaskStatus.COMPLETED for status in statuses)
    return round(completed * 100 / len(statuses), 2)
