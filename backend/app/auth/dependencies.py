from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.clerk import ClerkTokenVerifier, InvalidClerkTokenError
from app.core.config import get_settings
from app.db.session import get_session
from app.models.user import User
from app.services.users import get_or_create_user


bearer_scheme = HTTPBearer(auto_error=False)


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
) -> User:
    """Resolve the verified Clerk subject to its persistent application user."""
    return await get_or_create_user(session, clerk_subject)
