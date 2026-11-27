from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.models import Link, User
from app.services.learning_paths import (
    create_learning_path,
    create_stage,
    delete_learning_path,
    delete_stage,
)
from app.services.links import create_link, update_link
from app.services.tasks import create_task, delete_task


async def test_link_crud_and_sibling_title_uniqueness(
    db_session: AsyncSession,
) -> None:
    """Create, edit, and enforce unique titles for a path link."""
    db_session.add(User(clerk_subject="user_a"))
    await db_session.commit()
    path = await create_learning_path(db_session, "user_a", "Python")

    link = await create_link(
        db_session,
        "user_a",
        "path",
        path.id,
        "Docs",
        "https://example.com/docs",
    )

    await update_link(
        db_session,
        link,
        "Official Docs",
        "https://example.com/official",
    )

    assert link.title == "Official Docs"

    try:
        await create_link(
            db_session,
            "user_a",
            "path",
            path.id,
            "Official Docs",
            "https://example.com/duplicate",
        )
        assert False, "Duplicate link title should raise ApiError"

    except ApiError as error:
        assert error.status_code == 409


async def test_stage_and_path_deletion_remove_attached_links(
    db_session: AsyncSession,
) -> None:
    """Remove links attached to a stage and its tasks, then remove path links."""
    db_session.add(User(clerk_subject="user_a"))
    await db_session.commit()
    
    path = await create_learning_path(db_session, "user_a", "Python")
    stage = await create_stage(db_session, path, "Basics")
    task = await create_task(db_session, stage, "Variables")

    await create_link(db_session, "user_a", "path", path.id, "Path", "https://example.com/path")
    await create_link(db_session, "user_a", "stage", stage.id, "Stage", "https://example.com/stage")
    await create_link(db_session, "user_a", "task", task.id, "Task", "https://example.com/task")

    await delete_task(db_session, task)
    remaining_after_task = (await db_session.scalars(select(Link))).all()
    assert all(link.target_type != "task" for link in remaining_after_task)

    await delete_stage(db_session, stage)
    remaining = (await db_session.scalars(select(Link))).all()
    assert len(remaining) == 1
    assert remaining[0].target_type == "path"

    await delete_learning_path(db_session, path)
    assert (await db_session.scalars(select(Link))).all() == []
