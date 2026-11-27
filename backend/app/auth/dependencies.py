import logging
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.clerk import ClerkTokenVerifier, InvalidClerkTokenError
from app.core.config import get_settings
from app.core.errors import ApiError
from app.db.deletion_ledger import get_deletion_ledger_session
from app.db.session import get_session
from app.models.user import User
from app.services.account_deletion import is_subject_deleted
from app.services.users import get_or_create_user


bearer_scheme = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)


@lru_cache
def get_token_verifier() -> ClerkTokenVerifier:
    """Return the process-wide Clerk token verifier instance."""
    return ClerkTokenVerifier(get_settings())


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    verifier: ClerkTokenVerifier = Depends(get_token_verifier),
) -> str:
    """Authenticate a bearer request and return the verified user subject."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return await verifier.verify(credentials.credentials)
    
    except InvalidClerkTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


async def get_current_user(
    clerk_subject: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
    ledger_session: AsyncSession = Depends(get_deletion_ledger_session),
) -> User:
    """Reject deleted identities before resolving or creating application users."""
    try:
        deleted = await is_subject_deleted(ledger_session, clerk_subject)

    except SQLAlchemyError as error:
        logger.error("account_deletion_ledger_access_check_failed")
        raise ApiError(
            "deletion_ledger_unavailable",
            "Account access cannot be verified right now",
            503,
        ) from error

    if deleted:
        raise ApiError(
            "account_deleted",
            "This account is no longer available",
            403,
        )

    return await get_or_create_user(session, clerk_subject)
