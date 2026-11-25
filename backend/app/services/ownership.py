from typing import Any, Protocol, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class UserOwnedRecord(Protocol):
    id: Any
    user_id: Any


OwnedRecordType = TypeVar("OwnedRecordType", bound=UserOwnedRecord)


async def get_owned_record(
    session: AsyncSession,
    model: type[OwnedRecordType],
    record_id: object,
    user_id: str,
) -> OwnedRecordType | None:
    """Fetch a record only when both its identifier and owner match."""
    statement = select(model).where(model.id == record_id, model.user_id == user_id)
    return await session.scalar(statement)
