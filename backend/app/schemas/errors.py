from typing import Any

from pydantic import BaseModel


class ValidationIssueResponse(BaseModel):
    """Describe one field-level issue returned for invalid requests."""

    location: list[str | int]
    code: str
    message: str


class ApiErrorDetail(BaseModel):
    """Describe the stable code and client-safe message in an API error."""

    code: str
    message: str
    issues: list[ValidationIssueResponse] | None = None


class ApiErrorResponse(BaseModel):
    """Describe the common error envelope used by API exception handlers."""

    error: ApiErrorDetail


API_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {
        "model": ApiErrorResponse,
        "description": "Authentication is missing, invalid, or expired.",
    },
    403: {
        "model": ApiErrorResponse,
        "description": "The authenticated account cannot access this operation.",
    },
    404: {
        "model": ApiErrorResponse,
        "description": "The requested resource was not found or is not owned.",
    },
    409: {
        "model": ApiErrorResponse,
        "description": "The operation conflicts with existing data.",
    },
    422: {
        "model": ApiErrorResponse,
        "description": "Request or business-rule validation failed.",
    },
    503: {
        "model": ApiErrorResponse,
        "description": "A required service is temporarily unavailable.",
    },
}
