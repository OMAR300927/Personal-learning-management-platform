from sqlalchemy.ext.asyncio import AsyncSession

from app.services.users import get_or_create_user


async def test_get_or_create_user_persists_clerk_subject_and_timezone(
    db_session: AsyncSession,
) -> None:
    """Create a user from a Clerk subject with the default UTC timezone."""
    user = await get_or_create_user(db_session, "clerk_user_123")

    assert user.clerk_subject == "clerk_user_123"
    assert user.timezone == "UTC"


async def test_get_or_create_user_reuses_existing_record(
    db_session: AsyncSession,
) -> None:
    """Return the existing local user instead of creating a duplicate."""
    first_user = await get_or_create_user(db_session, "clerk_user_123")
    repeated_user = await get_or_create_user(db_session, "clerk_user_123")

    assert repeated_user.clerk_subject == first_user.clerk_subject
