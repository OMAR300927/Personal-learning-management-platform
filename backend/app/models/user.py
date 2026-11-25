from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    """Store the Clerk identity and product-specific timezone setting."""

    __tablename__ = "users"

    clerk_subject: Mapped[str] = mapped_column(String(255), primary_key=True)
    timezone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="UTC",
        server_default="UTC",
    )
