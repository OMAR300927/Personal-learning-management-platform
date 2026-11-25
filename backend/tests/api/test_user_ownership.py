from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.dependencies import get_current_user, get_current_user_id
from app.db.base import Base
from app.db.session import get_session
from app.models.user import User
from app.services.ownership import get_owned_record


class LearningRecord(Base):
    """Represent an owner-scoped record for API authorization tests."""

    __test__ = False
    __tablename__ = "test_learning_records"

    id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.clerk_subject"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(nullable=False)


class RecordUpdate(BaseModel):
    """Define the editable field accepted by the test-only API endpoint."""

    description: str


async def test_user_id(x_test_user: str = Header(alias="X-Test-User")) -> str:
    """Provide an isolated test identity in place of external JWT verification."""
    return x_test_user


async def test_user_ownership(
    db_session: AsyncSession,
) -> None:
    """Ensure one authenticated user cannot read or modify another user's record."""
    db_session.add_all(
        [
            User(clerk_subject="user_a"),
            User(clerk_subject="user_b"),
            LearningRecord(
                id="record_a",
                user_id="user_a",
                description="User A private record",
            ),
        ],
    )
    await db_session.commit()

    app = FastAPI()

    async def override_session() -> AsyncIterator[AsyncSession]:
        """Bind API requests to this test's isolated database session."""
        yield db_session

    @app.get("/records/{record_id}")
    async def read_record(
        record_id: str,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> dict[str, str]:
        """Return a record only when it belongs to the authenticated user."""
        record = await get_owned_record(
            session,
            LearningRecord,
            record_id,
            user.clerk_subject,
        )

        if record is None:
            raise HTTPException(status_code=404, detail="Record not found")
        
        return {"description": record.description}

    @app.patch("/records/{record_id}")
    async def update_record(
        record_id: str,
        update: RecordUpdate,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> dict[str, str]:
        """Update a record only after its owner-scoped lookup succeeds."""
        record = await get_owned_record(
            session,
            LearningRecord,
            record_id,
            user.clerk_subject,
        )

        if record is None:
            raise HTTPException(status_code=404, detail="Record not found")
        
        record.description = update.description
        await session.commit()
        return {"description": record.description}

    app.dependency_overrides[get_current_user_id] = test_user_id
    app.dependency_overrides[get_session] = override_session

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        owner_headers = {"X-Test-User": "user_a"}
        other_user_headers = {"X-Test-User": "user_b"}

        owner_read = await client.get("/records/record_a", headers=owner_headers)

        other_read = await client.get("/records/record_a", headers=other_user_headers)

        other_update = await client.patch(
            "/records/record_a",
            headers=other_user_headers,
            json={"description": "Unauthorized change"},
        )

        owner_read_after_denial = await client.get(
            "/records/record_a",
            headers=owner_headers,
        )
        
        owner_update = await client.patch(
            "/records/record_a",
            headers=owner_headers,
            json={"description": "Authorized change"},
        )

    assert owner_read.status_code == 200
    assert owner_read.json() == {"description": "User A private record"}
    assert other_read.status_code == 404
    assert other_update.status_code == 404
    assert owner_read_after_denial.json() == {"description": "User A private record"}
    assert owner_update.status_code == 200
    assert owner_update.json() == {"description": "Authorized change"}
