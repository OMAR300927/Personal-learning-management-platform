from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import LearningTimeEntry, Task, TaskStatus, User
from app.services.dashboard import get_dashboard
from app.services.learning_paths import create_learning_path, create_stage


async def test_dashboard_empty_and_current_periods(db_session: AsyncSession) -> None:
    """Return zeroed metrics and N/A path completion for empty data."""
    user = User(clerk_subject="user_a", timezone="UTC")
    db_session.add(user)
    await db_session.commit()

    result = await get_dashboard(db_session, user)

    assert result["completed_tasks"] == 0
    assert result["incomplete_tasks"] == 0
    assert result["paths"] == []
    assert result["week"]["total_learning_hours"] == 0 
    assert result["month"]["total_learning_hours"] == 0


async def test_dashboard_aggregates_hours_paths_and_task_counts(
    db_session: AsyncSession,
) -> None:
    """Aggregate learning hours, path completion, and task counts."""
    user = User(clerk_subject="user_a", timezone="UTC")
    db_session.add(user)
    await db_session.commit()

    path = await create_learning_path(db_session, "user_a", "Python")
    stage = await create_stage(db_session, path, "Basics")
    task_completed = Task(
        learning_path_id=path.id,
        stage_id=stage.id,
        user_id="user_a",
        title="Variables",
        position=0,
        status=TaskStatus.COMPLETED,
    )
    
    task_incomplete = Task(
        learning_path_id=path.id,
        stage_id=stage.id,
        user_id="user_a",
        title="Functions",
        position=1,
        status=TaskStatus.IN_PROGRESS,
    )
    db_session.add_all([task_completed, task_incomplete])
    db_session.add(
        LearningTimeEntry(
            user_id="user_a",
            learning_path_id=path.id,
            hours=2.5,
            occurred_at=datetime.now(timezone.utc),
            finalized=False,
        )
    )
    await db_session.commit()

    result = await get_dashboard(db_session, user)

    assert result["week"]["total_learning_hours"] == 2.5
    assert result["month"]["total_learning_hours"] == 2.5
    assert result["completed_tasks"] == 1
    assert result["incomplete_tasks"] == 1
    assert result["paths"][0]["completion_percentage"] == 50
