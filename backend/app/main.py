from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import router
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.db.deletion_ledger import DeletionLedgerSessionFactory
from app.db.session import SessionFactory
from app.services.account_deletion import replay_deletion_ledger


settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Replay deletion tombstones before allowing the API to serve requests."""
    async with (
        SessionFactory() as app_session,
        DeletionLedgerSessionFactory() as ledger_session,
    ):
        await replay_deletion_ledger(app_session, ledger_session)

    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)
register_error_handlers(app)
app.include_router(router, prefix=settings.api_prefix)
