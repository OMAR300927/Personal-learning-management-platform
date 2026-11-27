from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.stage import Stage


class LearningPath(Base):
    """Store an owner's learning path and its ordered stages."""

    __tablename__ = "learning_paths"
    __table_args__ = (
        UniqueConstraint("user_id", "title", name="uq_learning_paths_owner_title"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.clerk_subject", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    stages: Mapped[list["Stage"]] = relationship(
        back_populates="learning_path",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Stage.position",
    )
