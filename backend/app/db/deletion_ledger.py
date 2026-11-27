from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings


settings = get_settings()
ledger_engine = create_async_engine(settings.deletion_ledger_database_url, future=True)
DeletionLedgerSessionFactory = async_sessionmaker(
    ledger_engine,
    expire_on_commit=False,
)


async def get_deletion_ledger_session() -> AsyncIterator[AsyncSession]:
    """Yield a session connected to the independently managed deletion ledger."""
    async with DeletionLedgerSessionFactory() as session:
        yield session
