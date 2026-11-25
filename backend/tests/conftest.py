from collections.abc import AsyncIterator
from pathlib import Path

import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.base import Base
from app.models import User


@pytest_asyncio.fixture
async def test_engine(tmp_path: Path) -> AsyncIterator[AsyncEngine]:
    """Create a fresh temporary SQLite engine for one test invocation."""
    database_path = tmp_path / "test.db"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{database_path}",
        future=True,
    )

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    try:
        yield engine
        
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Yield a session bound exclusively to the temporary test engine."""
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
