import time
from typing import Any

import httpx
import jwt

from app.core.config import Settings


class InvalidClerkTokenError(Exception):
    """Raised when a Clerk token cannot be verified."""


class ClerkTokenVerifier:
    def __init__(self, settings: Settings, cache_ttl_seconds: int = 300) -> None:
        """Initialize JWT verification with settings and a JWKS cache lifetime."""
        self._settings = settings
        self._cache_ttl_seconds = cache_ttl_seconds
        self._cached_jwks: dict[str, Any] | None = None
        self._cached_at = 0.0

    async def verify(self, token: str) -> str:
        """Validate a Clerk JWT and return its trusted subject identifier."""
        if not self._settings.clerk_jwt_issuer:
            raise InvalidClerkTokenError("Clerk JWT settings are incomplete")
        
        if not self._settings.clerk_jwks_url:
            raise InvalidClerkTokenError("Clerk JWKS URL is not configured")
        authorized_parties = {
            party.strip()
            for party in self._settings.clerk_authorized_parties.split(",")
            if party.strip()
        }
        if not authorized_parties:
            raise InvalidClerkTokenError("Clerk authorized parties are not configured")

        try:
            header = jwt.get_unverified_header(token)
            if header.get("alg") != "RS256" or not header.get("kid"):
                raise InvalidClerkTokenError("Unsupported Clerk token header")

            jwks = await self._get_jwks()
            jwk = next(
                (key for key in jwks.get("keys", []) if key.get("kid") == header["kid"]),
                None,
            )

            if jwk is None:
                raise InvalidClerkTokenError("Clerk signing key was not found")

            signing_key = jwt.PyJWK.from_dict(jwk, algorithm="RS256")

            payload = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                issuer=self._settings.clerk_jwt_issuer,
                options={
                    "require": ["exp", "iss", "sub", "azp"],
                    "verify_aud": False,
                },
            )
            subject = payload.get("sub")
            authorized_party = payload.get("azp")

            if not isinstance(subject, str) or not subject:
                raise InvalidClerkTokenError("Clerk token subject is invalid")
            
            if not isinstance(authorized_party, str) or authorized_party not in authorized_parties:
                raise InvalidClerkTokenError("Clerk token authorized party is invalid")
            return subject
        
        except InvalidClerkTokenError:
            raise

        except (jwt.PyJWTError, ValueError, TypeError) as error:
            raise InvalidClerkTokenError("Clerk token verification failed") from error

    async def _get_jwks(self) -> dict[str, Any]:
        """Load signing keys from Clerk, reusing a short-lived in-memory cache."""
        now = time.monotonic()
        if self._cached_jwks is not None and now - self._cached_at < self._cache_ttl_seconds:
            return self._cached_jwks

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(self._settings.clerk_jwks_url)
                response.raise_for_status()
                jwks = response.json()
                
        except (httpx.HTTPError, ValueError) as error:
            raise InvalidClerkTokenError("Clerk signing keys could not be loaded") from error

        if not isinstance(jwks, dict) or not isinstance(jwks.get("keys"), list):
            raise InvalidClerkTokenError("Clerk signing keys response is invalid")

        self._cached_jwks = jwks
        self._cached_at = now
        return jwks
