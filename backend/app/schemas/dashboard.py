from typing import TypedDict

from pydantic import BaseModel


class DashboardPeriodData(TypedDict):
    """Represent the selected range and total hours for one period."""

    start: str
    end: str
    total_learning_hours: float


class DashboardPathData(TypedDict):
    """Represent one path's completion data."""

    id: int
    title: str
    completion_percentage: float | None


class DashboardGoalData(TypedDict):
    """Represent one goal's progress data."""

    id: int
    goal_type: str
    scope: str
    target: float
    progress: float
    progress_percentage: float


class DashboardData(TypedDict):
    """Represent the aggregate dashboard payload returned by the service."""

    week: DashboardPeriodData
    month: DashboardPeriodData
    paths: list[DashboardPathData]
    completed_tasks: int
    incomplete_tasks: int
    goals: list[DashboardGoalData]


class DashboardPathResponse(BaseModel):
    """Describe one path's completion in dashboard responses."""

    id: int
    title: str
    completion_percentage: float | None


class DashboardGoalResponse(BaseModel):
    """Describe goal progress shown on the dashboard."""

    id: int
    goal_type: str
    scope: str
    target: float
    progress: float
    progress_percentage: float


class DashboardPeriodResponse(BaseModel):
    """Describe a selected dashboard period."""

    start: str
    end: str
    total_learning_hours: float


class DashboardResponse(BaseModel):
    """Describe dashboard metrics for selected week and month periods."""

    week: DashboardPeriodResponse
    month: DashboardPeriodResponse
    paths: list[DashboardPathResponse]
    completed_tasks: int
    incomplete_tasks: int
    goals: list[DashboardGoalResponse]
