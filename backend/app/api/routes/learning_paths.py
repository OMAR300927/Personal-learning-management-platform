from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.errors import ApiError
from app.db.session import get_session
from app.models.user import User
from app.schemas.errors import API_ERROR_RESPONSES
from app.schemas.learning_paths import (
    LearningPathCreate,
    LearningPathDetailResponse,
    LearningPathReorder,
    LearningPathResponse,
    LearningPathUpdate,
    StageCreate,
    StageReorder,
    StageResponse,
    StageUpdate,
    TaskCreate,
    TaskReorder,
    TaskResponse,
    TaskStatusUpdate,
    TaskUpdate,
)
from app.services.learning_paths import (
    create_learning_path,
    create_stage,
    delete_learning_path,
    delete_stage,
    get_learning_path,
    get_stage,
    list_learning_paths,
    list_stages,
    reorder_learning_path,
    reorder_stage,
    update_learning_path,
    update_stage,
)
from app.services.tasks import (
    calculate_path_completion,
    change_task_status,
    create_task,
    delete_task,
    get_task,
    list_tasks,
    reorder_task,
    update_task,
)


router = APIRouter(
    prefix="/learning-paths",
    tags=["learning-paths"],
    responses=API_ERROR_RESPONSES,
)


@router.get("", response_model=list[LearningPathResponse])
async def list_paths(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[LearningPathResponse]:
    """List the authenticated user's learning paths."""
    paths = await list_learning_paths(session, user.clerk_subject)
    return [LearningPathResponse.model_validate(path, from_attributes=True) for path in paths]


@router.post("", response_model=LearningPathDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_path(
    request: LearningPathCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> LearningPathDetailResponse:
    """Create a learning path for the authenticated user."""
    path = await create_learning_path(session, user.clerk_subject, request.title)
    return LearningPathDetailResponse(
        id=path.id,
        title=path.title,
        position=path.position,
        stages=[],
        completion_percentage=None,
    )


@router.get("/{path_id}", response_model=LearningPathDetailResponse)
async def read_path(
    path_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> LearningPathDetailResponse:
    """Read one owned learning path and its stages."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    if path is None:
        raise ApiError("not_found", "Learning path not found", 404)
    
    stages = await list_stages(session, path)
    completion_percentage = await calculate_path_completion(
        session,
        user.clerk_subject,
        path.id,
    )
    return LearningPathDetailResponse(
        id=path.id,
        title=path.title,
        position=path.position,
        stages=[
            StageResponse.model_validate(stage, from_attributes=True)
            for stage in stages
        ],
        completion_percentage=completion_percentage,
    )


@router.patch("/{path_id}", response_model=LearningPathResponse)
async def edit_path(
    path_id: int,
    request: LearningPathUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> LearningPathResponse:
    """Edit an owned learning path."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    if path is None:
        raise ApiError("not_found", "Learning path not found", 404)
    
    path = await update_learning_path(session, path, request.title)
    return LearningPathResponse.model_validate(path, from_attributes=True)


@router.patch("/{path_id}/reorder", response_model=LearningPathResponse)
async def reorder_path(
    path_id: int,
    request: LearningPathReorder,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> LearningPathResponse:
    """Reorder an owned learning path."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    if path is None:
        raise ApiError("not_found", "Learning path not found", 404)
    
    path = await reorder_learning_path(session, path, request.position)
    return LearningPathResponse.model_validate(path, from_attributes=True)


@router.delete("/{path_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_path(
    path_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Delete an owned learning path and its stages."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    if path is None:
        raise ApiError("not_found", "Learning path not found", 404)
    
    await delete_learning_path(session, path)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{path_id}/stages", response_model=list[StageResponse])
async def list_path_stages(
    path_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[StageResponse]:
    """List stages belonging to an owned learning path."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    if path is None:
        raise ApiError("not_found", "Learning path not found", 404)
    
    stages = await list_stages(session, path)
    return [StageResponse.model_validate(stage, from_attributes=True) for stage in stages]


@router.post("/{path_id}/stages", response_model=StageResponse, status_code=status.HTTP_201_CREATED)
async def create_path_stage(
    path_id: int,
    request: StageCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> StageResponse:
    """Create a stage under an owned learning path."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    if path is None:
        raise ApiError("not_found", "Learning path not found", 404)
    
    stage = await create_stage(session, path, request.title)
    return StageResponse.model_validate(stage, from_attributes=True)


@router.patch("/{path_id}/stages/{stage_id}", response_model=StageResponse)
async def edit_stage(
    path_id: int,
    stage_id: int,
    request: StageUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> StageResponse:
    """Edit an owned stage in the specified path."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    stage = await get_stage(session, user.clerk_subject, stage_id) if path is not None else None
    if path is None or stage is None or stage.learning_path_id != path.id:
        raise ApiError("not_found", "Stage not found", 404)
    
    stage = await update_stage(session, stage, request.title)
    return StageResponse.model_validate(stage, from_attributes=True)


@router.patch("/{path_id}/stages/{stage_id}/reorder", response_model=StageResponse)
async def reorder_path_stage(
    path_id: int,
    stage_id: int,
    request: StageReorder,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> StageResponse:
    """Reorder an owned stage within its path."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    stage = await get_stage(session, user.clerk_subject, stage_id) if path is not None else None
    if path is None or stage is None or stage.learning_path_id != path.id:
        raise ApiError("not_found", "Stage not found", 404)
    
    stage = await reorder_stage(session, stage, request.position)
    return StageResponse.model_validate(stage, from_attributes=True)


@router.delete("/{path_id}/stages/{stage_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_stage(
    path_id: int,
    stage_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Delete an owned stage in the specified path."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    stage = await get_stage(session, user.clerk_subject, stage_id) if path is not None else None
    if path is None or stage is None or stage.learning_path_id != path.id:
        raise ApiError("not_found", "Stage not found", 404)
    
    await delete_stage(session, stage)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{path_id}/stages/{stage_id}/tasks",
    response_model=list[TaskResponse],
)
async def list_stage_tasks(
    path_id: int,
    stage_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[TaskResponse]:
    """List tasks belonging to an owned stage."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    stage = await get_stage(session, user.clerk_subject, stage_id) if path is not None else None
    if path is None or stage is None or stage.learning_path_id != path.id:
        raise ApiError("not_found", "Stage not found", 404)

    tasks = await list_tasks(session, stage)
    return [TaskResponse.model_validate(task, from_attributes=True) for task in tasks]


@router.post(
    "/{path_id}/stages/{stage_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_stage_task(
    path_id: int,
    stage_id: int,
    request: TaskCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> TaskResponse:
    """Create a task in an owned stage."""
    path = await get_learning_path(session, user.clerk_subject, path_id)
    stage = await get_stage(session, user.clerk_subject, stage_id) if path is not None else None
    if path is None or stage is None or stage.learning_path_id != path.id:
        raise ApiError("not_found", "Stage not found", 404)

    task = await create_task(session, stage, request.title)
    return TaskResponse.model_validate(task, from_attributes=True)


@router.patch(
    "/{path_id}/stages/{stage_id}/tasks/{task_id}",
    response_model=TaskResponse,
)
async def edit_task(
    path_id: int,
    stage_id: int,
    task_id: int,
    request: TaskUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> TaskResponse:
    """Edit an owned task without changing its stage."""
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

    task = await update_task(session, task, request.title)
    return TaskResponse.model_validate(task, from_attributes=True)


@router.patch(
    "/{path_id}/stages/{stage_id}/tasks/{task_id}/status",
    response_model=TaskResponse,
)
async def edit_task_status(
    path_id: int,
    stage_id: int,
    task_id: int,
    request: TaskStatusUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> TaskResponse:
    """Change an owned task status and append its status history."""
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

    task = await change_task_status(session, task, request.status)
    return TaskResponse.model_validate(task, from_attributes=True)


@router.patch(
    "/{path_id}/stages/{stage_id}/tasks/{task_id}/reorder",
    response_model=TaskResponse,
)
async def reorder_stage_task(
    path_id: int,
    stage_id: int,
    task_id: int,
    request: TaskReorder,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> TaskResponse:
    """Reorder an owned task within its stage."""
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

    task = await reorder_task(session, task, request.position)
    return TaskResponse.model_validate(task, from_attributes=True)


@router.delete(
    "/{path_id}/stages/{stage_id}/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_task(
    path_id: int,
    stage_id: int,
    task_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Delete an owned task without allowing cross-stage moves."""
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

    await delete_task(session, task)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
