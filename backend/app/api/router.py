from fastapi import APIRouter

from app.api.routes.account import router as account_router
from app.api.routes.learning_paths import router as learning_paths_router
from app.api.routes.links import router as links_router
from app.api.routes.learning_time import router as learning_time_router
from app.api.routes.learning_time import timezone_router
from app.api.routes.weekly_goals import router as weekly_goals_router
from app.api.routes.dashboard import router as dashboard_router


router = APIRouter()
router.include_router(account_router)
router.include_router(learning_paths_router)
router.include_router(links_router)
router.include_router(learning_time_router)
router.include_router(timezone_router)
router.include_router(weekly_goals_router)
router.include_router(dashboard_router)


@router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Return a lightweight response used to verify API availability."""
    return {"status": "ok"}
