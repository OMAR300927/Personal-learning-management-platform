from datetime import datetime

from pydantic import BaseModel, Field


class LearningTimeCreate(BaseModel):
    """Define fields accepted when recording learning time."""

    hours: float = Field(gt=0, le=24)
    occurred_at: datetime


class LearningTimeUpdate(BaseModel):
    """Define editable fields for an active-week entry."""

    hours: float = Field(gt=0, le=24)
    occurred_at: datetime


class LearningTimeResponse(BaseModel):
    """Describe a learning-time entry returned by the API."""

    id: int
    learning_path_id: int
    hours: float
    occurred_at: datetime
    finalized: bool


class TimezoneUpdate(BaseModel):
    """Define a timezone update for week-boundary recalculation."""

    timezone: str
