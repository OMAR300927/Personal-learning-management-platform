from collections.abc import AsyncIterator

import httpx
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.learning_paths import router as learning_paths_router
from app.api.routes.links import router as links_router
from app.auth.dependencies import get_current_user
from app.core.errors import register_error_handlers
from app.db.session import get_session
from app.models import User


async def test_link_api_supports_path_stage_and_task_links(
    db_session: AsyncSession,
) -> None:
    """Verify link CRUD and cross-user denial across supported targets."""
    db_session.add_all([User(clerk_subject="user_a"), User(clerk_subject="user_b")])
    await db_session.commit()

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(learning_paths_router)
    app.include_router(links_router)

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

        path_link = await client.post(
            f"/learning-paths/{path_id}/links",
            json={"title": "Docs", "url": "https://example.com/docs"},
        )

        stage_link = await client.post(
            f"/learning-paths/{path_id}/stages/{stage_id}/links",
            json={"title": "Guide", "url": "https://example.com/guide"},
        )
        
        task_link = await client.post(
            f"/learning-paths/{path_id}/stages/{stage_id}/tasks/{task_id}/links",
            json={"title": "Reference", "url": "https://example.com/reference"},
        )

        app.dependency_overrides[get_current_user] = override_user_b
        denied_edit = await client.patch(
            f"/learning-paths/{path_id}/links/{path_link.json()['id']}",
            json={"title": "Changed", "url": "https://example.com/changed"},
        )

        app.dependency_overrides[get_current_user] = override_user_a
        deleted_stage_link = await client.delete(
            f"/learning-paths/{path_id}/stages/{stage_id}/links/{stage_link.json()['id']}",
        )

    assert path_link.status_code == 201
    assert stage_link.status_code == 201
    assert task_link.status_code == 201
    assert denied_edit.status_code == 404
    assert deleted_stage_link.status_code == 204
