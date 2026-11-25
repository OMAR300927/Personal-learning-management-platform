import httpx
import pytest
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.core.errors import ApiError, register_error_handlers
from app.core.validation import LinkUrl, Title


class LinkRequest(BaseModel):
    """Describe the title and URL fields accepted by the test endpoint."""

    title: Title
    url: LinkUrl


@pytest.fixture
def validation_app() -> FastAPI:
    """Create an API instance with the project's request error handlers."""
    app = FastAPI()
    register_error_handlers(app)

    @app.post("/links")
    async def create_link(link: LinkRequest) -> dict[str, str]:
        """Return validated link data for response-format verification."""
        return {"title": link.title, "url": link.url}

    @app.get("/expected-error")
    async def expected_error() -> None:
        """Raise an application error to verify its normalized response."""
        raise ApiError("conflict", "Resource already exists", 409)

    @app.get("/http-error")
    async def http_error() -> None:
        """Raise an HTTP error to verify legacy exceptions are normalized."""
        raise HTTPException(status_code=404, detail="Resource not found")

    return app


async def test_valid_title_and_url_are_accepted(
    validation_app: FastAPI,
) -> None:
    """Accept values at the approved title and URL lengths."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=validation_app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/links",
            json={"title": "Learning resource", "url": "https://example.com/learn"},
        )

    assert response.status_code == 200
    assert response.json()["title"] == "Learning resource"


async def test_title_over_100_characters_returns_structured_validation_error(
    validation_app: FastAPI,
) -> None:
    """Reject an overlong title with the shared client-error shape."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=validation_app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/links",
            json={"title": "t" * 101, "url": "https://example.com"},
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["error"]["issues"][0]["location"] == ["body", "title"]


async def test_url_over_2048_characters_is_rejected(
    validation_app: FastAPI,
) -> None:
    """Reject URLs that exceed the approved maximum length."""
    oversized_url = f"https://example.com/{'a' * 2030}"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=validation_app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/links",
            json={"title": "Resource", "url": oversized_url},
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["error"]["issues"][0]["location"] == ["body", "url"]


async def test_invalid_url_is_rejected(
    validation_app: FastAPI,
) -> None:
    """Reject values that are not valid absolute HTTP(S) URLs."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=validation_app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/links",
            json={"title": "Resource", "url": "not a URL"},
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_url_type_preserves_exact_maximum_length() -> None:
    """Confirm a syntactically valid URL at exactly 2,048 characters is accepted."""
    url = f"https://example.com/{'a' * (2048 - len('https://example.com/'))}"

    assert len(url) == 2048
    assert LinkRequest(title="Resource", url=url).url == url


async def test_application_errors_use_shared_error_envelope(
    validation_app: FastAPI,
) -> None:
    """Keep application error codes and messages in the common response shape."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=validation_app),
        base_url="http://test",
    ) as client:
        response = await client.get("/expected-error")

    assert response.status_code == 409
    assert response.json() == {
        "error": {"code": "conflict", "message": "Resource already exists"},
    }


async def test_http_errors_use_shared_error_envelope(
    validation_app: FastAPI,
) -> None:
    """Normalize HTTP exceptions without changing their status code."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=validation_app),
        base_url="http://test",
    ) as client:
        response = await client.get("/http-error")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "http_error", "message": "Resource not found"},
    }
