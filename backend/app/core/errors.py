from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    """Represent an expected API failure with a stable code and HTTP status."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        """Store client-safe error information for the registered handler."""
        self.code = code
        self.message = message
        self.status_code = status_code
        self.headers = headers


async def handle_api_error(request: Request, error: Exception) -> JSONResponse:
    """Return expected application errors in the shared response format."""
    if not isinstance(error, ApiError):
        raise TypeError("ApiError handler received an unexpected exception")

    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": {
                "code": error.code,
                "message": error.message,
            },
        },
        headers=error.headers,
    )


async def handle_http_error(request: Request, error: Exception) -> JSONResponse:
    """Normalize FastAPI HTTP errors while preserving status and response headers."""
    if not isinstance(error, HTTPException):
        raise TypeError("HTTP error handler received an unexpected exception")

    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": {
                "code": "http_error",
                "message": str(error.detail),
            },
        },
        headers=error.headers,
    )


async def handle_validation_error(
    request: Request,
    error: Exception,
) -> JSONResponse:
    """Return validation locations and messages without echoing submitted data."""
    if not isinstance(error, RequestValidationError):
        raise TypeError("Validation error handler received an unexpected exception")

    issues: list[dict[str, Any]] = [
        {
            "location": list(issue["loc"]),
            "code": issue["type"],
            "message": issue["msg"],
        }
        for issue in error.errors()
    ]
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Request validation failed",
                "issues": issues,
            },
        },
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register consistent handlers for API and request-validation failures."""
    app.add_exception_handler(ApiError, handle_api_error)
    app.add_exception_handler(HTTPException, handle_http_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
