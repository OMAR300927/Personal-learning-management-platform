from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.models import LearningPath, Stage, User
from app.services.learning_paths import (
    create_learning_path,
    create_stage,
    delete_learning_path,
    delete_stage,
    reorder_learning_path,
    reorder_stage,
    update_learning_path,
)


async def test_learning_path_and_stage_crud_rules(db_session: AsyncSession) -> None:
    """Create, rename, reorder, and delete paths and stages atomically."""
    db_session.add(User(clerk_subject="user_a"))
    await db_session.commit()

    first = await create_learning_path(db_session, "user_a", "Python")
    second = await create_learning_path(db_session, "user_a", "Math")
    stage = await create_stage(db_session, first, "Basics")

    assert first.position == 0
    assert second.position == 1

    await reorder_learning_path(db_session, second, 0)
    assert second.position == 0

    await update_learning_path(db_session, first, "Python Advanced")
    assert first.title == "Python Advanced"

    await reorder_stage(db_session, stage, 0)
    assert stage.position == 0

    await delete_stage(db_session, stage)
    remaining = (await db_session.scalars(select(Stage))).all()
    assert remaining == []

    await delete_learning_path(db_session, first)
    await db_session.delete(second)
    await db_session.commit()
    assert (await db_session.scalars(select(LearningPath))).all() == []


async def test_sibling_titles_are_unique(db_session: AsyncSession) -> None:
    """Reject duplicate path titles and duplicate stage titles."""
    db_session.add(User(clerk_subject="user_a"))
    await db_session.commit()
    path = await create_learning_path(db_session, "user_a", "Python")
    await create_stage(db_session, path, "Basics")

    try:
        await create_learning_path(db_session, "user_a", "Python")
        assert False, "Duplicate path title should raise ApiError"
    except ApiError as error:
        assert error.status_code == 409

    try:
        await create_stage(db_session, path, "Basics")
        assert False, "Duplicate stage title should raise ApiError"
    except ApiError as error:
        assert error.status_code == 409
