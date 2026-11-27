import logging

from fastapi import APIRouter, Depends, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_id
from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.db.deletion_ledger import get_deletion_ledger_session
from app.db.session import get_session
from app.schemas.account import AccountDeletionResponse
from app.schemas.errors import API_ERROR_RESPONSES
from app.services.account_deletion import delete_account


logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/account",
    tags=["account"],
    responses=API_ERROR_RESPONSES,
)


@router.delete(
    "",
    response_model=AccountDeletionResponse,
    responses={
        202: {
            "model": AccountDeletionResponse,
            "description": "Deletion is accepted; Clerk deletion remains pending.",
        },
    },
)
async def delete_current_account(
    response: Response,
    clerk_subject: str = Depends(get_current_user_id),
    app_session: AsyncSession = Depends(get_session),
    ledger_session: AsyncSession = Depends(get_deletion_ledger_session),
    settings: Settings = Depends(get_settings),
) -> AccountDeletionResponse:
    """Delete the authenticated user's app data and request Clerk deletion."""
    try:
        completed = await delete_account(
            app_session,
            ledger_session,
            clerk_subject,
            settings,
        )

    except SQLAlchemyError as error:
        logger.error("account_deletion_database_failure")
        raise ApiError(
            "account_deletion_incomplete",
            "Account deletion could not be completed and will be retried",
            503,
        ) from error

    if completed:
        return AccountDeletionResponse(status="completed")

    response.status_code = 202
    return AccountDeletionResponse(status="pending")
