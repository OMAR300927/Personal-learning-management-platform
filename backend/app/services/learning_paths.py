from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ApiError
from app.models.learning_path import LearningPath
from app.models.stage import Stage
from app.models.task import Task
from app.models.learning_time import LearningTimeEntry
from app.models.weekly_goal import WeeklyGoal
from app.services.links import delete_target_links


async def _next_position(
    session: AsyncSession,
    model: type[LearningPath] | type[Stage],
    owner_filter,
) -> int:
    """Return the next position at the end of an owner's ordered sibling list."""
    statement = select(model.position).where(owner_filter).order_by(model.position.desc()).limit(1)
    position = await session.scalar(statement)
    return (position + 1) if position is not None else 0


async def list_learning_paths(session: AsyncSession, user_id: str) -> Sequence[LearningPath]:
    """List a user's learning paths in their configured order."""
    statement = (
        select(LearningPath)
        .where(LearningPath.user_id == user_id)
        .order_by(LearningPath.position, LearningPath.id)
    )
    return (await session.scalars(statement)).all()


async def get_learning_path(
    session: AsyncSession,
    user_id: str,
    path_id: int,
) -> LearningPath | None:
    """Fetch one owned learning path with its stages."""
    statement = (
        select(LearningPath)
        .options(selectinload(LearningPath.stages))
        .where(LearningPath.id == path_id, LearningPath.user_id == user_id)
    )
    return await session.scalar(statement)


async def create_learning_path(
    session: AsyncSession,
    user_id: str,
    title: str,
) -> LearningPath:
    """Create a path with the next available position."""
    existing = await session.scalar(
        select(LearningPath.id).where(
            LearningPath.user_id == user_id,
            LearningPath.title == title,
        )
    )
    if existing is not None:
        raise ApiError("conflict", "A learning path with this title already exists", 409)

    position = await _next_position(
        session,
        LearningPath,
        LearningPath.user_id == user_id,
    )

    learning_path = LearningPath(user_id=user_id, title=title, position=position)
    session.add(learning_path)
    await session.commit()
    await session.refresh(learning_path)
    return learning_path


async def update_learning_path(
    session: AsyncSession,
    learning_path: LearningPath,
    title: str,
) -> LearningPath:
    """Rename an owned path after checking sibling-title uniqueness."""
    existing = await session.scalar(
        select(LearningPath.id).where(
            LearningPath.user_id == learning_path.user_id,
            LearningPath.title == title,
            LearningPath.id != learning_path.id,
        )
    )
    if existing is not None:
        raise ApiError("conflict", "A learning path with this title already exists", 409)

    learning_path.title = title
    await session.commit()
    await session.refresh(learning_path)
    return learning_path


async def delete_learning_path(
    session: AsyncSession,
    learning_path: LearningPath,
) -> None:
    """Delete a path and normalize its owner's remaining sibling positions."""
    user_id = learning_path.user_id
    path_id = learning_path.id
    stage_ids = (
        await session.scalars(
            select(Stage.id).where(Stage.learning_path_id == path_id)
        )
    ).all()

    task_ids = (
        await session.scalars(
            select(Task.id).where(Task.learning_path_id == path_id)
        )
    ).all()
    
    await session.execute(
        delete(LearningTimeEntry).where(
            LearningTimeEntry.learning_path_id == path_id
        )
    )
    
    await session.execute(
        delete(WeeklyGoal).where(
            WeeklyGoal.learning_path_id == path_id
        )
    )

    await delete_target_links(session, "path", path_id)
    for stage_id in stage_ids:
        await delete_target_links(session, "stage", stage_id)

    for task_id in task_ids:
        await delete_target_links(session, "task", task_id)

    await session.delete(learning_path)
    await session.flush()

    siblings = (
        await session.scalars(
            select(LearningPath)
            .where(LearningPath.user_id == user_id)
            .order_by(LearningPath.position, LearningPath.id)
        )
    ).all()

    for index, sibling in enumerate(siblings):
        sibling.position = index
    await session.commit()


async def reorder_learning_path(
    session: AsyncSession,
    learning_path: LearningPath,
    position: int,
) -> LearningPath:
    """Move an owned path and normalize sibling positions."""
    if position < 0:
        raise ApiError("validation_error", "Position must be zero or greater", 422)

    siblings = (
        await session.scalars(
            select(LearningPath)
            .where(LearningPath.user_id == learning_path.user_id)
            .order_by(LearningPath.position, LearningPath.id)
        )
    ).all()

    siblings = [item for item in siblings if item.id != learning_path.id]
    position = min(position, len(siblings))
    siblings.insert(position, learning_path)

    for index, item in enumerate(siblings):
        item.position = index

    await session.commit()
    await session.refresh(learning_path)
    return learning_path


async def list_stages(
    session: AsyncSession,
    learning_path: LearningPath,
) -> Sequence[Stage]:
    """List a path's stages in their configured order."""
    statement = (
        select(Stage)
        .where(Stage.learning_path_id == learning_path.id, Stage.user_id == learning_path.user_id)
        .order_by(Stage.position, Stage.id)
    )
    return (await session.scalars(statement)).all()


async def create_stage(
    session: AsyncSession,
    learning_path: LearningPath,
    title: str,
) -> Stage:
    """Create a stage under an owned path."""
    existing = await session.scalar(
        select(Stage.id).where(
            Stage.learning_path_id == learning_path.id,
            Stage.title == title,
        )
    )
    if existing is not None:
        raise ApiError("conflict", "A stage with this title already exists", 409)

    position = await _next_position(
        session,
        Stage,
        Stage.learning_path_id == learning_path.id,
    )

    stage = Stage(
        learning_path_id=learning_path.id,
        user_id=learning_path.user_id,
        title=title,
        position=position,
    )

    session.add(stage)
    await session.commit()
    await session.refresh(stage)
    return stage


async def get_stage(
    session: AsyncSession,
    user_id: str,
    stage_id: int,
) -> Stage | None:
    """Fetch one owned stage."""
    statement = select(Stage).where(Stage.id == stage_id, Stage.user_id == user_id)
    return await session.scalar(statement)


async def update_stage(
    session: AsyncSession,
    stage: Stage,
    title: str,
) -> Stage:
    """Rename an owned stage after checking sibling-title uniqueness."""
    existing = await session.scalar(
        select(Stage.id).where(
            Stage.learning_path_id == stage.learning_path_id,
            Stage.title == title,
            Stage.id != stage.id,
        )
    )

    if existing is not None:
        raise ApiError("conflict", "A stage with this title already exists", 409)

    stage.title = title
    await session.commit()
    await session.refresh(stage)
    return stage


async def delete_stage(session: AsyncSession, stage: Stage) -> None:
    """Delete a stage and atomically normalize remaining sibling positions."""
    learning_path_id = stage.learning_path_id
    stage_id = stage.id
    task_ids = (
        await session.scalars(select(Task.id).where(Task.stage_id == stage_id))
    ).all()
    
    await delete_target_links(session, "stage", stage_id)
    for task_id in task_ids:
        await delete_target_links(session, "task", task_id)

    await session.delete(stage)
    await session.flush()

    siblings = (
        await session.scalars(
            select(Stage)
            .where(Stage.learning_path_id == learning_path_id)
            .order_by(Stage.position, Stage.id)
        )
    ).all()

    for index, sibling in enumerate(siblings):
        sibling.position = index
    await session.commit()


async def reorder_stage(
    session: AsyncSession,
    stage: Stage,
    position: int,
) -> Stage:
    """Move an owned stage and normalize sibling positions."""
    if position < 0:
        raise ApiError("validation_error", "Position must be zero or greater", 422)

    siblings = (
        await session.scalars(
            select(Stage)
            .where(Stage.learning_path_id == stage.learning_path_id)
            .order_by(Stage.position, Stage.id)
        )
    ).all()
    
    siblings = [item for item in siblings if item.id != stage.id]
    position = min(position, len(siblings))
    siblings.insert(position, stage)

    for index, item in enumerate(siblings):
        item.position = index
    await session.commit()
    await session.refresh(stage)
    return stage
