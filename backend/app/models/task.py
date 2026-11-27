from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.stage import Stage


class TaskStatus(str, enum.Enum):
    """Represent the supported lifecycle states for a learning task."""

    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"


class Task(Base):
    """Store an ordered task owned through a stage and learning path."""

    __tablename__ = "tasks"
    __table_args__ = (
        UniqueConstraint("stage_id", "title", name="uq_tasks_stage_title"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    learning_path_id: Mapped[int] = mapped_column(
        ForeignKey("learning_paths.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stage_id: Mapped[int] = mapped_column(
        ForeignKey("stages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.clerk_subject", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status", native_enum=False),
        nullable=False,
        default=TaskStatus.NOT_STARTED,
    )

    stage: Mapped["Stage"] = relationship(back_populates="tasks")


class TaskStatusHistory(Base):
    """Record a timestamped task-status state for week-boundary reconstruction."""

    __tablename__ = "task_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )
    learning_path_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.clerk_subject", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status", native_enum=False),
        nullable=False,
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
