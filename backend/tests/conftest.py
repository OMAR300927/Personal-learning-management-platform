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
from app.db.deletion_ledger_base import DeletionLedgerBase
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


@pytest_asyncio.fixture
async def test_ledger_engine(tmp_path: Path) -> AsyncIterator[AsyncEngine]:
    """Create an isolated temporary database for deletion-ledger tests."""
    database_path = tmp_path / "deletion-ledger.db"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{database_path}",
        future=True,
    )

    async with engine.begin() as connection:
        await connection.run_sync(DeletionLedgerBase.metadata.create_all)

    try:
        yield engine

    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def ledger_session(test_ledger_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Yield a session bound only to the isolated temporary deletion ledger."""
    session_factory = async_sessionmaker(
        test_ledger_engine,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session
