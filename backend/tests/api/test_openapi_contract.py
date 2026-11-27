from app.main import app


def test_openapi_documents_authentication_and_common_errors() -> None:
    """Expose bearer auth and the shared error envelope on protected operations."""
    schema = app.openapi()
    bearer_scheme = schema["components"]["securitySchemes"]["HTTPBearer"]
    assert bearer_scheme["type"] == "http"
    assert bearer_scheme["scheme"] == "bearer"

    for path, path_item in schema["paths"].items():
        for method, operation in path_item.items():
            if method not in {"get", "post", "patch", "put", "delete"}:
                continue
            
            if path == "/api/v1/health":
                assert "security" not in operation
                continue

            assert operation["security"] == [{"HTTPBearer": []}]
            for status_code in ("401", "403", "404", "409", "422", "503"):
                assert status_code in operation["responses"]
                response_schema = operation["responses"][status_code]["content"][
                    "application/json"
                ]["schema"]
                assert response_schema["$ref"].endswith("/ApiErrorResponse")


def test_openapi_documents_pending_account_deletion_response() -> None:
    """Describe the 202 response returned while Clerk deletion is pending."""
    response = app.openapi()["paths"]["/api/v1/account"]["delete"]["responses"]["202"]

    assert response["description"] == (
        "Deletion is accepted; Clerk deletion remains pending."
    )
    assert response["content"]["application/json"]["schema"]["$ref"].endswith(
        "/AccountDeletionResponse"
    )
