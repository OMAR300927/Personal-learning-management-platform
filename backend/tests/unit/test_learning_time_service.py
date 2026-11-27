from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.services.learning_paths import create_learning_path
from app.services.learning_time import (
    create_learning_time_entry,
    delete_learning_time_entry,
    update_learning_time_entry,
    update_user_timezone,
)


async def test_learning_time_validation_and_timezone_recalculation(
    db_session: AsyncSession,
) -> None:
    """Accept fractional hours, reject invalid values, and update user timezone."""
    from app.models import User

    user = User(clerk_subject="user_a")
    db_session.add(user)
    await db_session.commit()
    path = await create_learning_path(db_session, user.clerk_subject, "Python")

    entry = await create_learning_time_entry(
        db_session,
        user,
        path.id,
        1.5,
        datetime.now(timezone.utc),
    )

    assert entry.hours == 1.5

    try:
        await create_learning_time_entry(
            db_session,
            user,
            path.id,
            0,
            datetime.now(timezone.utc),
        )
        assert False, "Zero hours should raise ApiError"

    except ApiError as error:
        assert error.status_code == 422

    await update_user_timezone(db_session, user, "Europe/London")
    assert user.timezone == "Europe/London"


async def test_ended_learning_time_entry_cannot_be_changed_or_deleted(
    db_session: AsyncSession,
) -> None:
    """Lock entries in weeks that have already ended."""
    from app.models import User

    user = User(clerk_subject="user_a")
    db_session.add(user)
    await db_session.commit()

    path = await create_learning_path(db_session, user.clerk_subject, "Python")
    old_time = datetime.now(timezone.utc) - timedelta(days=30)
    entry = await create_learning_time_entry(
        db_session,
        user,
        path.id,
        2,
        datetime.now(timezone.utc),
    )

    entry.occurred_at = old_time
    await db_session.commit()

    try:
        await update_learning_time_entry(
            db_session,
            entry,
            user,
            3,
            old_time,
        )
        assert False, "Ended entry should raise ApiError"

    except ApiError as error:
        assert error.status_code == 409

    try:
        await delete_learning_time_entry(db_session, entry, user)
        assert False, "Ended entry should raise ApiError"
        
    except ApiError as error:
        assert error.status_code == 409
