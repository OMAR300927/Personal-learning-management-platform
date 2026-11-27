from typing import Literal

from pydantic import BaseModel


class AccountDeletionResponse(BaseModel):
    """Report whether Clerk identity deletion completed or remains pending."""

    status: Literal["completed", "pending"]
