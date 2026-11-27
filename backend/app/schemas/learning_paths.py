from pydantic import BaseModel

from app.core.validation import Title
from app.models.task import TaskStatus


class StageCreate(BaseModel):
    """Define fields accepted when creating a stage."""

    title: Title


class StageUpdate(BaseModel):
    """Define fields accepted when editing a stage."""

    title: Title


class StageReorder(BaseModel):
    """Define the requested stage position."""

    position: int


class StageResponse(BaseModel):
    """Describe a stage returned by the API."""

    id: int
    learning_path_id: int
    title: str
    position: int


class LearningPathCreate(BaseModel):
    """Define fields accepted when creating a learning path."""

    title: Title


class LearningPathUpdate(BaseModel):
    """Define fields accepted when editing a learning path."""

    title: Title


class LearningPathReorder(BaseModel):
    """Define the requested learning-path position."""

    position: int


class LearningPathResponse(BaseModel):
    """Describe a learning path returned by the API."""

    id: int
    title: str
    position: int


class LearningPathDetailResponse(LearningPathResponse):
    """Describe a learning path with its ordered stages."""

    stages: list[StageResponse]
    completion_percentage: float | None


class TaskCreate(BaseModel):
    """Define fields accepted when creating a task."""

    title: Title


class TaskUpdate(BaseModel):
    """Define fields accepted when editing a task."""

    title: Title


class TaskStatusUpdate(BaseModel):
    """Define a task status transition."""

    status: TaskStatus


class TaskReorder(BaseModel):
    """Define the requested task position."""

    position: int


class TaskResponse(BaseModel):
    """Describe a task returned by the API."""

    id: int
    learning_path_id: int
    stage_id: int
    title: str
    position: int
    status: TaskStatus
