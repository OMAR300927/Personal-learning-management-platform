from pydantic import BaseModel, Field

from app.models.weekly_goal import WeeklyGoalScope, WeeklyGoalType


class WeeklyGoalCreate(BaseModel):
    """Define fields accepted when creating a weekly goal."""

    goal_type: WeeklyGoalType
    scope: WeeklyGoalScope
    learning_path_id: int | None = None
    target: float = Field(gt=0)


class WeeklyGoalUpdate(BaseModel):
    """Define fields accepted when editing a current-week goal."""

    target: float = Field(gt=0)


class WeeklyGoalResponse(BaseModel):
    """Describe a weekly goal and its active progress."""

    id: int
    learning_path_id: int | None
    week_start: str
    goal_type: WeeklyGoalType
    scope: WeeklyGoalScope
    target: float
    progress: float
    progress_percentage: float
