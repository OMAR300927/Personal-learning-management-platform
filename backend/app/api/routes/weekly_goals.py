from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.errors import ApiError
from app.db.session import get_session
from app.models.user import User
from app.schemas.errors import API_ERROR_RESPONSES
from app.schemas.weekly_goals import (
    WeeklyGoalCreate,
    WeeklyGoalResponse,
    WeeklyGoalUpdate,
)
from app.services.learning_paths import get_learning_path
from app.services.weekly_goals import (
    calculate_goal_progress,
    create_weekly_goal,
    get_weekly_goal,
    list_weekly_goals,
    update_weekly_goal,
)


router = APIRouter(
    prefix="/weekly-goals",
    tags=["weekly-goals"],
    responses=API_ERROR_RESPONSES,
)


async def _response(
    session: AsyncSession,
    user: User,
    goal,
) -> WeeklyGoalResponse:
    """Build a goal response with capped active progress."""
    progress, percentage = await calculate_goal_progress(session, user, goal)
    return WeeklyGoalResponse(
        id=goal.id,
        learning_path_id=goal.learning_path_id,
        week_start=goal.week_start.isoformat(),
        goal_type=goal.goal_type,
        scope=goal.scope,
        target=goal.target,
        progress=progress,
        progress_percentage=percentage,
    )


@router.get("", response_model=list[WeeklyGoalResponse])
async def list_goals(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[WeeklyGoalResponse]:
    """List goals for the user's current Saturday-Friday week."""
    goals = await list_weekly_goals(session, user)
    return [await _response(session, user, goal) for goal in goals]


@router.post("", response_model=WeeklyGoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    request: WeeklyGoalCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> WeeklyGoalResponse:
    """Create an overall or path-specific goal for the current week."""
    if request.learning_path_id is not None:
        path = await get_learning_path(
            session,
            user.clerk_subject,
            request.learning_path_id,
        )

        if path is None:
            raise ApiError("not_found", "Learning path not found", 404)

    goal = await create_weekly_goal(
        session,
        user,
        request.goal_type,
        request.scope,
        request.learning_path_id,
        request.target,
    )
    return await _response(session, user, goal)


@router.patch("/{goal_id}", response_model=WeeklyGoalResponse)
async def edit_goal(
    goal_id: int,
    request: WeeklyGoalUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> WeeklyGoalResponse:
    """Edit an owned goal only for the current week."""
    goal = await get_weekly_goal(session, user.clerk_subject, goal_id)
    if goal is None:
        raise ApiError("not_found", "Weekly goal not found", 404)
    
    goal = await update_weekly_goal(session, user, goal, request.target)
    return await _response(session, user, goal)
