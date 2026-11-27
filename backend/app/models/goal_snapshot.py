from datetime import date, datetime, timezone

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.weekly_goal import WeeklyGoalScope, WeeklyGoalType


class GoalSnapshot(Base):
    """Store an immutable snapshot of finalized weekly-goal progress."""

    __tablename__ = "goal_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "goal_id",
            "week_start",
            name="uq_goal_snapshots_goal_week",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    goal_id: Mapped[int] = mapped_column(
        ForeignKey("weekly_goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.clerk_subject", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    learning_path_id: Mapped[int | None] = mapped_column(
        ForeignKey("learning_paths.id", ondelete="SET NULL"),
        nullable=True,
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
    target: Mapped[float] = mapped_column(Float, nullable=False)
    progress: Mapped[float] = mapped_column(Float, nullable=False)
    progress_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    finalized_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
