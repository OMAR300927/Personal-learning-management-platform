import enum
from datetime import date

from sqlalchemy import Date, Enum, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WeeklyGoalType(str, enum.Enum):
    """Represent supported weekly goal target types."""

    LEARNING_HOURS = "learning_hours"
    COMPLETED_TASKS = "completed_tasks"


class WeeklyGoalScope(str, enum.Enum):
    """Represent overall and path-specific goal scopes."""

    OVERALL = "overall"
    LEARNING_PATH = "learning_path"


class WeeklyGoal(Base):
    """Store a fixed-week overall or path-specific weekly goal."""

    __tablename__ = "weekly_goals"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "week_start",
            "goal_type",
            "scope_key",
            name="uq_weekly_goals_week_type_scope",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.clerk_subject", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    learning_path_id: Mapped[int | None] = mapped_column(
        ForeignKey("learning_paths.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    goal_type: Mapped[WeeklyGoalType] = mapped_column(
        Enum(WeeklyGoalType, name="weekly_goal_type", native_enum=False),
        nullable=False,
    )
    scope: Mapped[WeeklyGoalScope] = mapped_column(
        Enum(WeeklyGoalScope, name="weekly_goal_scope", native_enum=False),
        nullable=False,
    )
    scope_key: Mapped[str] = mapped_column(String(64), nullable=False)
    target: Mapped[float] = mapped_column(Float, nullable=False)
