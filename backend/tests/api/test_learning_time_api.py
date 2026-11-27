from collections.abc import AsyncIterator
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.learning_time import router, timezone_router
from app.api.routes.learning_paths import router as learning_paths_router
from app.auth.dependencies import get_current_user
from app.core.errors import register_error_handlers
from app.db.session import get_session
from app.models import User


async def test_learning_time_api_ownership_and_validation(
    db_session: AsyncSession,
) -> None:
    """Verify entry CRUD and cross-user denial through HTTP."""
    db_session.add_all([User(clerk_subject="user_a"), User(clerk_subject="user_b")])
    await db_session.commit()

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(learning_paths_router)
    app.include_router(router)
    app.include_router(timezone_router)

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
        
        entry = await client.post(
            f"/learning-paths/{path_id}/learning-time",
            json={
                "hours": 1.25,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        entry_id = entry.json()["id"]
        
        invalid = await client.post(
            f"/learning-paths/{path_id}/learning-time",
            json={
                "hours": 25,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        app.dependency_overrides[get_current_user] = override_user_b
        denied = await client.patch(
            f"/learning-paths/{path_id}/learning-time/{entry_id}",
            json={
                "hours": 2,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        app.dependency_overrides[get_current_user] = override_user_a
        timezone_response = await client.patch(
            "/users/me/timezone",
            json={"timezone": "Europe/London"},
        )

    assert entry.status_code == 201
    assert entry.json()["hours"] == 1.25
    assert invalid.status_code == 422
    assert denied.status_code == 404
    assert timezone_response.status_code == 200
