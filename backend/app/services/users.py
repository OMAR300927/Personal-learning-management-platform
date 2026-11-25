from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_or_create_user(session: AsyncSession, clerk_subject: str) -> User:
    """Return the local user for a verified Clerk subject, creating it if absent."""
    user = await session.get(User, clerk_subject)
    if user is not None:
        return user

    user = User(clerk_subject=clerk_subject)
    session.add(user)

    try:
        await session.commit()

    except IntegrityError:
        await session.rollback()
        user = await session.get(User, clerk_subject)

        if user is None:
            raise
        
        return user

    await session.refresh(user)
    return user
