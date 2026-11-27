from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.lib.week import (
    is_ended_week,
    saturday_friday_week,
    validate_timezone,
)
from app.models.learning_time import LearningTimeEntry
from app.models.user import User


def ensure_active_entry(
    entry: LearningTimeEntry,
    timezone_name: str,
    now: datetime | None = None,
) -> None:
    """Reject mutation when an entry belongs to finalized or ended history."""
    entry_week_start, _ = saturday_friday_week(entry.occurred_at, timezone_name)
    moment = now or datetime.now(timezone.utc)
    current_week_start, _ = saturday_friday_week(moment, timezone_name)
    if (
        entry.finalized
        or is_ended_week(entry.occurred_at, timezone_name, moment)
        or entry_week_start != current_week_start
    ):
        raise ApiError(
            "conflict",
            "Learning-time entries in ended weeks cannot be changed",
            409,
        )


async def list_learning_time_entries(
    session: AsyncSession,
    user_id: str,
    learning_path_id: int,
) -> Sequence[LearningTimeEntry]:
    """List owned entries for one path in occurrence-time order."""
    statement = (
        select(LearningTimeEntry)
        .where(
            LearningTimeEntry.user_id == user_id,
            LearningTimeEntry.learning_path_id == learning_path_id,
        )
        .order_by(LearningTimeEntry.occurred_at.desc(), LearningTimeEntry.id.desc())
    )
    return (await session.scalars(statement)).all()


async def create_learning_time_entry(
    session: AsyncSession,
    user: User,
    learning_path_id: int,
    hours: float,
    occurred_at: datetime,
) -> LearningTimeEntry:
    """Create a learning-time entry only in an active week."""
    if hours <= 0 or hours > 24:
        raise ApiError(
            "validation_error",
            "Hours must be greater than zero and at most 24",
            422,
        )
    validate_timezone(user.timezone)
    if occurred_at.tzinfo is None:
        occurred_at = occurred_at.replace(tzinfo=timezone.utc)

    entry = LearningTimeEntry(
        user_id=user.clerk_subject,
        learning_path_id=learning_path_id,
        hours=hours,
        occurred_at=occurred_at,
        finalized=False,
    )
    ensure_active_entry(entry, user.timezone)
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


async def get_learning_time_entry(
    session: AsyncSession,
    user_id: str,
    entry_id: int,
) -> LearningTimeEntry | None:
    """Fetch one owned learning-time entry."""
    statement = select(LearningTimeEntry).where(
        LearningTimeEntry.id == entry_id,
        LearningTimeEntry.user_id == user_id,
    )
    return await session.scalar(statement)


async def update_learning_time_entry(
    session: AsyncSession,
    entry: LearningTimeEntry,
    user: User,
    hours: float,
    occurred_at: datetime,
) -> LearningTimeEntry:
    """Edit an active-week entry and preserve its path association."""
    if hours <= 0 or hours > 24:
        raise ApiError(
            "validation_error",
            "Hours must be greater than zero and at most 24",
            422,
        )
    
    ensure_active_entry(entry, user.timezone)
    if occurred_at.tzinfo is None:
        occurred_at = occurred_at.replace(tzinfo=timezone.utc)

    entry.hours = hours
    entry.occurred_at = occurred_at
    ensure_active_entry(entry, user.timezone)
    await session.commit()
    await session.refresh(entry)
    return entry


async def delete_learning_time_entry(
    session: AsyncSession,
    entry: LearningTimeEntry,
    user: User,
) -> None:
    """Delete an entry only while its recalculated week is active."""
    ensure_active_entry(entry, user.timezone)
    await session.delete(entry)
    await session.commit()


async def update_user_timezone(
    session: AsyncSession,
    user: User,
    timezone_name: str,
) -> User:
    """Update timezone after validating it; unfinalized entries regroup dynamically."""
    validate_timezone(timezone_name)
    user.timezone = timezone_name
    await session.commit()
    await session.refresh(user)
    return user
