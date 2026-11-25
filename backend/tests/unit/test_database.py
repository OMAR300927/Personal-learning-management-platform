from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def test_database_session_uses_isolated_sqlite_database(
    db_session: AsyncSession,
) -> None:
    """Verify the test fixture can execute a query in isolated SQLite."""
    result = await db_session.execute(text("select 1"))

    assert result.scalar_one() == 1
