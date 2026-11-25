from fastapi import FastAPI

from app.api.router import router
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging


settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)
register_error_handlers(app)
app.include_router(router, prefix=settings.api_prefix)
