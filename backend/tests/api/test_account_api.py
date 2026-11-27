from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

import app.main as main
from app.api.routes.account import router as account_router
from app.auth.dependencies import get_current_user, get_current_user_id
from app.core.config import Settings, get_settings
from app.core.errors import register_error_handlers
from app.db.deletion_ledger import get_deletion_ledger_session
from app.db.session import get_session
from app.models import LearningPath, User
from app.models.deletion_record import DeletionRecord


async def _test_subject() -> str:
    """Provide a deterministic verified subject for account API tests."""
    return "user_a"


async def test_account_deletion_api_returns_pending_without_server_secret(
    db_session: AsyncSession,
    ledger_session: AsyncSession,
) -> None:
    """Accept deletion, block access, and report a pending Clerk retry honestly."""
    db_session.add(User(clerk_subject="user_a"))
    await db_session.commit()

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(account_router)

    async def override_session() -> AsyncIterator[AsyncSession]:
        """Bind requests to the isolated application database."""
        yield db_session

    async def override_ledger_session() -> AsyncIterator[AsyncSession]:
        """Bind requests to the isolated deletion ledger."""
        yield ledger_session

    def override_settings() -> Settings:
        """Ensure no real Clerk secret is used by this test."""
        return Settings(clerk_secret_key="")

    app.dependency_overrides[get_current_user_id] = _test_subject
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_deletion_ledger_session] = override_ledger_session
    app.dependency_overrides[get_settings] = override_settings

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.delete("/account")

    assert response.status_code == 202
    assert response.json() == {"status": "pending"}
    assert await db_session.get(User, "user_a") is None
    assert await ledger_session.get(DeletionRecord, "user_a") is not None


async def test_deleted_subject_is_blocked_before_local_user_creation(
    db_session: AsyncSession,
    ledger_session: AsyncSession,
) -> None:
    """Reject a ledgered identity before get-or-create can restore access."""
    ledger_session.add(DeletionRecord(clerk_subject="user_a"))
    await ledger_session.commit()

    app = FastAPI()
    register_error_handlers(app)

    @app.get("/protected")
    async def protected(user: User = Depends(get_current_user)) -> dict[str, str]:
        """Expose the current subject only for this access-control test."""
        return {"subject": user.clerk_subject}

    async def override_session() -> AsyncIterator[AsyncSession]:
        """Bind the protected request to the isolated application database."""
        yield db_session

    async def override_ledger_session() -> AsyncIterator[AsyncSession]:
        """Bind the protected request to the isolated deletion ledger."""
        yield ledger_session

    app.dependency_overrides[get_current_user_id] = _test_subject
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_deletion_ledger_session] = override_ledger_session

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/protected")

    assert response.status_code == 403
    assert await db_session.get(User, "user_a") is None


async def test_application_startup_replays_ledger_before_serving(
    test_engine: AsyncEngine,
    test_ledger_engine: AsyncEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Replay deletion tombstones during lifespan startup before serving."""
    app_sessions = async_sessionmaker(test_engine, expire_on_commit=False)
    ledger_sessions = async_sessionmaker(
        test_ledger_engine,
        expire_on_commit=False,
    )
    async with app_sessions() as session:
        user = User(clerk_subject="user_a")
        session.add(user)
        await session.flush()
        session.add(LearningPath(user_id="user_a", title="Restored", position=0))
        await session.commit()

    async with ledger_sessions() as session:
        session.add(DeletionRecord(clerk_subject="user_a"))
        await session.commit()

    monkeypatch.setattr(main, "SessionFactory", app_sessions)
    monkeypatch.setattr(main, "DeletionLedgerSessionFactory", ledger_sessions)

    async with main.lifespan(FastAPI()):
        async with app_sessions() as session:
            assert await session.get(User, "user_a") is None
            assert await session.scalar(
                select(LearningPath).where(LearningPath.user_id == "user_a"),
            ) is None
