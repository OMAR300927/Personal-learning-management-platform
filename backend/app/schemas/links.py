from pydantic import BaseModel

from app.core.validation import LinkUrl, Title


class LinkCreate(BaseModel):
    """Define fields accepted when creating a link."""

    title: Title
    url: LinkUrl


class LinkUpdate(BaseModel):
    """Define fields accepted when editing a link."""

    title: Title
    url: LinkUrl


class LinkResponse(BaseModel):
    """Describe a link returned by the API."""

    id: int
    target_type: str
    target_id: int
    title: str
    url: str
