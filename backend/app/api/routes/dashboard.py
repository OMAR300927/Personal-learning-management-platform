from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.errors import ApiError
from app.db.session import get_session
from app.models.user import User
from app.schemas.dashboard import DashboardResponse
from app.schemas.errors import API_ERROR_RESPONSES
from app.services.dashboard import get_dashboard


router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    responses=API_ERROR_RESPONSES,
)


@router.get("", response_model=DashboardResponse)
async def read_dashboard(
    week: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DashboardResponse:
    """Return dashboard metrics for selected week and month periods."""
    try:
        dashboard = await get_dashboard(session, user, week, month)

    except ValueError as error:
        raise ApiError("validation_error", str(error), 422) from error
    
    return DashboardResponse.model_validate(dashboard)
