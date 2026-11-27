from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.errors import ApiError
from app.db.session import get_session
from app.models.user import User
from app.schemas.errors import API_ERROR_RESPONSES
from app.schemas.learning_time import (
    LearningTimeCreate,
    LearningTimeResponse,
    LearningTimeUpdate,
    TimezoneUpdate,
)
from app.services.learning_paths import get_learning_path
from app.services.learning_time import (
    create_learning_time_entry,
    delete_learning_time_entry,
    get_learning_time_entry,
    list_learning_time_entries,
    update_learning_time_entry,
    update_user_timezone,
)


router = APIRouter(
    prefix="/learning-paths",
    tags=["learning-time"],
    responses=API_ERROR_RESPONSES,
)


@router.get("/{path_id}/learning-time", response_model=list[LearningTimeResponse])
async def list_entries(
    path_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[LearningTimeResponse]:
    """List owned learning-time entries for one path."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    if path is None:
        raise ApiError("not_found", "Learning path not found", 404)
    entries = await list_learning_time_entries(session, user.clerk_subject, path.id)
    return [
        LearningTimeResponse.model_validate(entry, from_attributes=True)
        for entry in entries
    ]


@router.post(
    "/{path_id}/learning-time",
    response_model=LearningTimeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_entry(
    path_id: int,
    request: LearningTimeCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> LearningTimeResponse:
    """Record learning time for an owned path's active week."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    if path is None:
        raise ApiError("not_found", "Learning path not found", 404)
    
    entry = await create_learning_time_entry(
        session,
        user,
        path.id,
        request.hours,
        request.occurred_at,
    )
    return LearningTimeResponse.model_validate(entry, from_attributes=True)


@router.patch(
    "/{path_id}/learning-time/{entry_id}",
    response_model=LearningTimeResponse,
)
async def edit_entry(
    path_id: int,
    entry_id: int,
    request: LearningTimeUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> LearningTimeResponse:
    """Edit an owned active-week learning-time entry."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    entry = (
        await get_learning_time_entry(session, user.clerk_subject, entry_id)
        if path is not None
        else None
    )

    if path is None or entry is None or entry.learning_path_id != path.id:
        raise ApiError("not_found", "Learning-time entry not found", 404)
    
    entry = await update_learning_time_entry(
        session,
        entry,
        user,
        request.hours,
        request.occurred_at,
    )
    return LearningTimeResponse.model_validate(entry, from_attributes=True)


@router.delete(
    "/{path_id}/learning-time/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_entry(
    path_id: int,
    entry_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Delete an owned active-week learning-time entry."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    entry = (
        await get_learning_time_entry(session, user.clerk_subject, entry_id)
        if path is not None
        else None
    )

    if path is None or entry is None or entry.learning_path_id != path.id:
        raise ApiError("not_found", "Learning-time entry not found", 404)
    
    await delete_learning_time_entry(session, entry, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


timezone_router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses=API_ERROR_RESPONSES,
)


@timezone_router.patch("/me/timezone", response_model=dict[str, str])
async def change_timezone(
    request: TimezoneUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Update the timezone used to recalculate unfinalized week boundaries."""
    try:
        await update_user_timezone(session, user, request.timezone)

    except ValueError as error:
        raise ApiError("validation_error", str(error), 422) from error
    
    return {"timezone": user.timezone}
