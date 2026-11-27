from collections.abc import AsyncIterator

import httpx
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.learning_paths import router as learning_paths_router
from app.api.routes.weekly_goals import router
from app.auth.dependencies import get_current_user
from app.core.errors import register_error_handlers
from app.db.session import get_session
from app.models import User


async def test_weekly_goal_api_validation_and_ownership(
    db_session: AsyncSession,
) -> None:
    """Verify current-week goal creation and cross-user denial."""
    db_session.add_all([User(clerk_subject="user_a"), User(clerk_subject="user_b")])
    await db_session.commit()

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(learning_paths_router)
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
        created = await client.post(
            "/weekly-goals",
            json={
                "goal_type": "learning_hours",
                "scope": "overall",
                "target": 5,
            },
        )
        goal_id = created.json()["id"]
        
        duplicate = await client.post(
            "/weekly-goals",
            json={
                "goal_type": "learning_hours",
                "scope": "overall",
                "target": 8,
            },
        )

        app.dependency_overrides[get_current_user] = override_user_b
        denied = await client.patch(
            f"/weekly-goals/{goal_id}",
            json={"target": 10},
        )

    assert created.status_code == 201
    assert created.json()["progress_percentage"] == 0
    assert duplicate.status_code == 409
    assert denied.status_code == 404
