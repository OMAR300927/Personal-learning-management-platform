from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.errors import ApiError
from app.db.session import get_session
from app.models.user import User
from app.schemas.errors import API_ERROR_RESPONSES
from app.schemas.links import LinkCreate, LinkResponse, LinkUpdate
from app.services.learning_paths import get_learning_path, get_stage
from app.services.links import (
    create_link,
    delete_link,
    get_link,
    list_links,
    update_link,
)
from app.services.tasks import get_task


router = APIRouter(
    prefix="/learning-paths",
    tags=["links"],
    responses=API_ERROR_RESPONSES,
)


def _validate_link_response(link) -> LinkResponse:
    """Convert a link model to its API response."""
    return LinkResponse.model_validate(link, from_attributes=True)


@router.get("/{path_id}/links", response_model=list[LinkResponse])
async def list_path_links(
    path_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[LinkResponse]:
    """List links attached to an owned learning path."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    if path is None:
        raise ApiError("not_found", "Learning path not found", 404)
    
    links = await list_links(session, user.clerk_subject, "path", path.id)
    return [_validate_link_response(link) for link in links]


@router.post("/{path_id}/links", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def create_path_link(
    path_id: int,
    request: LinkCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> LinkResponse:
    """Create a link attached to an owned learning path."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    if path is None:
        raise ApiError("not_found", "Learning path not found", 404)
    
    link = await create_link(
        session,
        user.clerk_subject,
        "path",
        path.id,
        request.title,
        request.url,
    )
    return _validate_link_response(link)


@router.patch("/{path_id}/links/{link_id}", response_model=LinkResponse)
async def edit_path_link(
    path_id: int,
    link_id: int,
    request: LinkUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> LinkResponse:
    """Edit a link attached to an owned learning path."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    link = (
        await get_link(session, user.clerk_subject, link_id, "path", path.id)
        if path is not None
        else None
    )

    if path is None or link is None:
        raise ApiError("not_found", "Link not found", 404)
    
    link = await update_link(session, link, request.title, request.url)
    return _validate_link_response(link)


@router.delete("/{path_id}/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_path_link(
    path_id: int,
    link_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Delete a link attached to an owned learning path."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    link = (
        await get_link(session, user.clerk_subject, link_id, "path", path.id)
        if path is not None
        else None
    )

    if path is None or link is None:
        raise ApiError("not_found", "Link not found", 404)
    
    await delete_link(session, link)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{path_id}/stages/{stage_id}/links", response_model=list[LinkResponse])
async def list_stage_links(
    path_id: int,
    stage_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[LinkResponse]:
    """List links attached to an owned stage."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    stage = await get_stage(session, user.clerk_subject, stage_id) if path is not None else None
    if path is None or stage is None or stage.learning_path_id != path.id:
        raise ApiError("not_found", "Stage not found", 404)
    
    links = await list_links(session, user.clerk_subject, "stage", stage.id)
    return [_validate_link_response(link) for link in links]


@router.post(
    "/{path_id}/stages/{stage_id}/links",
    response_model=LinkResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_stage_link(
    path_id: int,
    stage_id: int,
    request: LinkCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> LinkResponse:
    """Create a link attached to an owned stage."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    stage = await get_stage(session, user.clerk_subject, stage_id) if path is not None else None
    if path is None or stage is None or stage.learning_path_id != path.id:
        raise ApiError("not_found", "Stage not found", 404)
    
    link = await create_link(
        session,
        user.clerk_subject,
        "stage",
        stage.id,
        request.title,
        request.url,
    )
    return _validate_link_response(link)


@router.patch(
    "/{path_id}/stages/{stage_id}/links/{link_id}",
    response_model=LinkResponse,
)
async def edit_stage_link(
    path_id: int,
    stage_id: int,
    link_id: int,
    request: LinkUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> LinkResponse:
    """Edit a link attached to an owned stage."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    stage = await get_stage(session, user.clerk_subject, stage_id) if path is not None else None
    link = (
        await get_link(session, user.clerk_subject, link_id, "stage", stage.id)
        if stage is not None
        else None
    )

    if path is None or stage is None or stage.learning_path_id != path.id or link is None:
        raise ApiError("not_found", "Link not found", 404)
    
    link = await update_link(session, link, request.title, request.url)
    return _validate_link_response(link)


@router.delete(
    "/{path_id}/stages/{stage_id}/links/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_stage_link(
    path_id: int,
    stage_id: int,
    link_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Delete a link attached to an owned stage."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    stage = await get_stage(session, user.clerk_subject, stage_id) if path is not None else None
    link = (
        await get_link(session, user.clerk_subject, link_id, "stage", stage.id)
        if stage is not None
        else None
    )

    if path is None or stage is None or stage.learning_path_id != path.id or link is None:
        raise ApiError("not_found", "Link not found", 404)
    
    await delete_link(session, link)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{path_id}/stages/{stage_id}/tasks/{task_id}/links",
    response_model=list[LinkResponse],
)
async def list_task_links(
    path_id: int,
    stage_id: int,
    task_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[LinkResponse]:
    """List links attached to an owned task."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    stage = await get_stage(session, user.clerk_subject, stage_id) if path is not None else None
    task = await get_task(session, user.clerk_subject, task_id) if stage is not None else None
    if (
        path is None
        or stage is None
        or task is None
        or stage.learning_path_id != path.id
        or task.stage_id != stage.id
    ):
        raise ApiError("not_found", "Task not found", 404)
    
    links = await list_links(session, user.clerk_subject, "task", task.id)
    return [_validate_link_response(link) for link in links]


@router.post(
    "/{path_id}/stages/{stage_id}/tasks/{task_id}/links",
    response_model=LinkResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task_link(
    path_id: int,
    stage_id: int,
    task_id: int,
    request: LinkCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> LinkResponse:
    """Create a link attached to an owned task."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    stage = await get_stage(session, user.clerk_subject, stage_id) if path is not None else None
    task = await get_task(session, user.clerk_subject, task_id) if stage is not None else None
    if (
        path is None
        or stage is None
        or task is None
        or stage.learning_path_id != path.id
        or task.stage_id != stage.id
    ):
        raise ApiError("not_found", "Task not found", 404)
    
    link = await create_link(
        session,
        user.clerk_subject,
        "task",
        task.id,
        request.title,
        request.url,
    )
    return _validate_link_response(link)


@router.patch(
    "/{path_id}/stages/{stage_id}/tasks/{task_id}/links/{link_id}",
    response_model=LinkResponse,
)
async def edit_task_link(
    path_id: int,
    stage_id: int,
    task_id: int,
    link_id: int,
    request: LinkUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> LinkResponse:
    """Edit a link attached to an owned task."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    stage = await get_stage(session, user.clerk_subject, stage_id) if path is not None else None
    task = await get_task(session, user.clerk_subject, task_id) if stage is not None else None
    link = (
        await get_link(session, user.clerk_subject, link_id, "task", task.id)
        if task is not None
        else None
    )

    if (
        path is None
        or stage is None
        or task is None
        or link is None
        or stage.learning_path_id != path.id
        or task.stage_id != stage.id
    ):
        raise ApiError("not_found", "Link not found", 404)
    
    link = await update_link(session, link, request.title, request.url)
    return _validate_link_response(link)


@router.delete(
    "/{path_id}/stages/{stage_id}/tasks/{task_id}/links/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_task_link(
    path_id: int,
    stage_id: int,
    task_id: int,
    link_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Delete a link attached to an owned task."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    stage = await get_stage(session, user.clerk_subject, stage_id) if path is not None else None
    task = await get_task(session, user.clerk_subject, task_id) if stage is not None else None
    link = (
        await get_link(session, user.clerk_subject, link_id, "task", task.id)
        if task is not None
        else None
    )

    if (
        path is None
        or stage is None
        or task is None
        or link is None
        or stage.learning_path_id != path.id
        or task.stage_id != stage.id
    ):
        raise ApiError("not_found", "Link not found", 404)
    
    await delete_link(session, link)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
