from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException

from app.auth.clerk import ClerkTokenVerifier, InvalidClerkTokenError
from app.auth.dependencies import get_current_user_id
from app.core.config import Settings


@pytest.fixture
def signing_key() -> rsa.RSAPrivateKey:
    """Create an RSA private key for deterministic JWT verification tests."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def verifier(signing_key: rsa.RSAPrivateKey) -> ClerkTokenVerifier:
    """Build a Clerk verifier backed by the test key set."""
    public_key = signing_key.public_key()
    public_numbers = public_key.public_numbers()
    jwk = {
        "kty": "RSA",
        "kid": "test-key",
        "alg": "RS256",
        "use": "sig",
        "n": jwt.utils.base64url_encode(
            public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, "big"),
        ).decode(),
        "e": jwt.utils.base64url_encode(
            public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, "big"),
        ).decode(),
    }

    instance = ClerkTokenVerifier(
        Settings(
            clerk_jwt_issuer="https://issuer.example",
            clerk_jwks_url="https://issuer.example/.well-known/jwks.json",
            clerk_authorized_parties="http://localhost:5173,https://app.example",
        ),
    )

    async def get_jwks() -> dict[str, list[dict[str, str]]]:
        """Return the test signing key without making a network request."""
        return {"keys": [jwk]}

    instance._get_jwks = get_jwks  # type: ignore[method-assign]
    return instance


def create_token(
    signing_key: rsa.RSAPrivateKey,
    **claims: str | datetime,
) -> str:
    """Create a signed test token with valid default Clerk claims."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "user_123",
        "iss": "https://issuer.example",
        "azp": "http://localhost:5173",
        "iat": now,
        "exp": now + timedelta(minutes=5),
        **claims,
    }
    return jwt.encode(payload, signing_key, algorithm="RS256", headers={"kid": "test-key"})


async def test_valid_clerk_token_resolves_subject(
    verifier: ClerkTokenVerifier,
    signing_key: rsa.RSAPrivateKey,
) -> None:
    """Verify that a valid Clerk token resolves to its subject."""
    assert await verifier.verify(create_token(signing_key)) == "user_123"


@pytest.mark.parametrize(
    "claims",
    [
        {"exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        {"iss": "https://wrong-issuer.example"},
        {"azp": "https://attacker.example"},
        {"azp": None},
    ],
)
async def test_invalid_clerk_claims_are_rejected(
    verifier: ClerkTokenVerifier,
    signing_key: rsa.RSAPrivateKey,
    claims: dict[str, str | datetime],
) -> None:
    """Verify that invalid issuer, origin, or expiry claims are rejected."""
    with pytest.raises(InvalidClerkTokenError):
        await verifier.verify(create_token(signing_key, **claims))


async def test_malformed_token_is_rejected(verifier: ClerkTokenVerifier) -> None:
    """Verify that malformed JWT input raises the verification error."""
    with pytest.raises(InvalidClerkTokenError):
        await verifier.verify("not-a-jwt")


async def test_missing_bearer_credentials_are_rejected() -> None:
    """Verify that requests without bearer credentials receive HTTP 401."""
    with pytest.raises(HTTPException) as error:
        await get_current_user_id(credentials=None)

    assert error.value.status_code == 401
