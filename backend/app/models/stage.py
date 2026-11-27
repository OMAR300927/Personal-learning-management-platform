from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.learning_path import LearningPath
    from app.models.task import Task


class Stage(Base):
    """Store an ordered stage owned through a learning path."""

    __tablename__ = "stages"
    __table_args__ = (
        UniqueConstraint("learning_path_id", "title", name="uq_stages_path_title"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    learning_path_id: Mapped[int] = mapped_column(
        ForeignKey("learning_paths.id", ondelete="CASCADE"),
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

    learning_path: Mapped["LearningPath"] = relationship(back_populates="stages")
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="stage",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Task.position",
    )
