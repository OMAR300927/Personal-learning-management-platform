from collections.abc import AsyncIterator

import httpx
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.learning_paths import router
from app.auth.dependencies import get_current_user
from app.core.errors import register_error_handlers
from app.db.session import get_session
from app.models import User


async def test_task_api_status_completion_and_ownership(
    db_session: AsyncSession,
) -> None:
    """Verify task CRUD, status transitions, completion, and ownership through HTTP."""
    db_session.add_all([User(clerk_subject="user_a"), User(clerk_subject="user_b")])
    await db_session.commit()

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(router)

    async def override_user_a() -> User:
        """Return the first test identity."""
        user = await db_session.get(User, "user_a")
        assert user is not None, "Test user_a was not found"
        return user

    async def override_user_b() -> User:
        """Return the second test identity."""
        user = await db_session.get(User, "user_b")
        assert user is not None, "Test user_b was not found"
        return user

    async def override_session() -> AsyncIterator[AsyncSession]:
        """Yield the isolated test session."""
        yield db_session

    app.dependency_overrides[get_session] = override_session

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        app.dependency_overrides[get_current_user] = override_user_a
        path = await client.post("/learning-paths", json={"title": "Python"})
        path_id = path.json()["id"]
        stage = await client.post(
            f"/learning-paths/{path_id}/stages",
            json={"title": "Basics"},
        )
        stage_id = stage.json()["id"]
        task = await client.post(
            f"/learning-paths/{path_id}/stages/{stage_id}/tasks",
            json={"title": "Variables"},
        )
        task_id = task.json()["id"]

        completed = await client.patch(
            f"/learning-paths/{path_id}/stages/{stage_id}/tasks/{task_id}/status",
            json={"status": "Completed"},
        )
        back_to_progress = await client.patch(
            f"/learning-paths/{path_id}/stages/{stage_id}/tasks/{task_id}/status",
            json={"status": "In Progress"},
        )
        path_detail = await client.get(f"/learning-paths/{path_id}")

        app.dependency_overrides[get_current_user] = override_user_b
        denied_task = await client.patch(
            f"/learning-paths/{path_id}/stages/{stage_id}/tasks/{task_id}",
            json={"title": "Changed"},
        )

        app.dependency_overrides[get_current_user] = override_user_a
        deleted = await client.delete(
            f"/learning-paths/{path_id}/stages/{stage_id}/tasks/{task_id}",
        )

    assert task.status_code == 201
    assert completed.json()["status"] == "Completed"
    assert back_to_progress.json()["status"] == "In Progress"
    assert path_detail.json()["completion_percentage"] == 0.0
    assert denied_task.status_code == 404
    assert deleted.status_code == 204
