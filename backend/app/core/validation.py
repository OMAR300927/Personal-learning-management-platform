from typing import Annotated

from pydantic import AfterValidator, HttpUrl, StringConstraints, TypeAdapter


_http_url_adapter = TypeAdapter(HttpUrl)


def validate_http_url(value: str) -> str:
    """Validate an absolute HTTP(S) URL while preserving its original text."""
    _http_url_adapter.validate_python(value)
    return value


Title = Annotated[str, StringConstraints(max_length=100)]
LinkUrl = Annotated[
    str,
    StringConstraints(max_length=2048),
    AfterValidator(validate_http_url),
]
