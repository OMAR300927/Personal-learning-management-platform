from collections.abc import AsyncIterator

import httpx
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.learning_paths import router
from app.auth.dependencies import get_current_user
from app.core.errors import register_error_handlers
from app.db.session import get_session
from app.models import User


async def test_learning_paths_api_enforces_owner_and_crud(
    db_session: AsyncSession,
) -> None:
    """Verify path ownership, stage CRUD, ordering, and deletion through HTTP."""
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

        created = await client.post("/learning-paths", json={"title": "Python"})
        path_id = created.json()["id"]

        stage_created = await client.post(
            f"/learning-paths/{path_id}/stages",
            json={"title": "Basics"},
        )
        stage_id = stage_created.json()["id"]

        app.dependency_overrides[get_current_user] = override_user_b
        denied_read = await client.get(f"/learning-paths/{path_id}")
        denied_stage_edit = await client.patch(
            f"/learning-paths/{path_id}/stages/{stage_id}",
            json={"title": "Changed"},
        )

        app.dependency_overrides[get_current_user] = override_user_a
        reordered = await client.patch(
            f"/learning-paths/{path_id}/reorder",
            json={"position": 0},
        )
        removed_stage = await client.delete(
            f"/learning-paths/{path_id}/stages/{stage_id}",
        )
        removed_path = await client.delete(f"/learning-paths/{path_id}")

    assert created.status_code == 201
    assert stage_created.status_code == 201
    assert denied_read.status_code == 404
    assert denied_stage_edit.status_code == 404
    assert reordered.status_code == 200
    assert removed_stage.status_code == 204
    assert removed_path.status_code == 204
