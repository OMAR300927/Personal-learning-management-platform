from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.models.link import Link


async def list_links(
    session: AsyncSession,
    user_id: str,
    target_type: str,
    target_id: int,
) -> Sequence[Link]:
    """List an owner's links for one supported target."""
    statement = (
        select(Link)
        .where(
            Link.user_id == user_id,
            Link.target_type == target_type,
            Link.target_id == target_id,
        )
        .order_by(Link.id)
    )
    return (await session.scalars(statement)).all()


async def create_link(
    session: AsyncSession,
    user_id: str,
    target_type: str,
    target_id: int,
    title: str,
    url: str,
) -> Link:
    """Create a link after enforcing sibling-title uniqueness."""
    existing = await session.scalar(
        select(Link.id).where(
            Link.user_id == user_id,
            Link.target_type == target_type,
            Link.target_id == target_id,
            Link.title == title,
        )
    )
    if existing is not None:
        raise ApiError("conflict", "A link with this title already exists", 409)

    link = Link(
        user_id=user_id,
        target_type=target_type,
        target_id=target_id,
        title=title,
        url=url,
    )
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link


async def get_link(
    session: AsyncSession,
    user_id: str,
    link_id: int,
    target_type: str,
    target_id: int,
) -> Link | None:
    """Fetch one owned link attached to the exact target."""
    statement = select(Link).where(
        Link.id == link_id,
        Link.user_id == user_id,
        Link.target_type == target_type,
        Link.target_id == target_id,
    )
    return await session.scalar(statement)


async def update_link(
    session: AsyncSession,
    link: Link,
    title: str,
    url: str,
) -> Link:
    """Edit a link after checking sibling-title uniqueness."""
    existing = await session.scalar(
        select(Link.id).where(
            Link.user_id == link.user_id,
            Link.target_type == link.target_type,
            Link.target_id == link.target_id,
            Link.title == title,
            Link.id != link.id,
        )
    )
    if existing is not None:
        raise ApiError("conflict", "A link with this title already exists", 409)

    link.title = title
    link.url = url
    await session.commit()
    await session.refresh(link)
    return link


async def delete_link(session: AsyncSession, link: Link) -> None:
    """Delete one owned link."""
    await session.delete(link)
    await session.commit()


async def delete_target_links(
    session: AsyncSession,
    target_type: str,
    target_id: int,
) -> None:
    """Delete all links attached to one target."""
    await session.execute(
        delete(Link).where(
            Link.target_type == target_type,
            Link.target_id == target_id,
        )
    )
