from collections.abc import AsyncIterator

import httpx
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.dashboard import router
from app.auth.dependencies import get_current_user
from app.core.errors import register_error_handlers
from app.db.session import get_session
from app.models import User


async def test_dashboard_api_navigation_and_ownership(
    db_session: AsyncSession,
) -> None:
    """Verify current and explicit period dashboard requests."""
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

    async def override_session() -> AsyncIterator[AsyncSession]:
        """Yield the isolated test session."""
        yield db_session

    app.dependency_overrides[get_current_user] = override_user_a
    app.dependency_overrides[get_session] = override_session

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        current = await client.get("/dashboard")
        navigated = await client.get(
            "/dashboard",
            params={"week": "2025-12-27", "month": "2025-12"},
        )
        invalid = await client.get("/dashboard", params={"week": "bad"})

    assert current.status_code == 200
    assert current.json()["paths"] == []
    assert navigated.status_code == 200
    assert navigated.json()["week"]["start"] == "2025-12-27"
    assert navigated.json()["month"]["start"] == "2025-12-01"
    assert invalid.status_code == 422
