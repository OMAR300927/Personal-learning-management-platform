from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Personal Learning Management Platform API"
    app_version: str = "0.1.0"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    database_url: str = "sqlite+aiosqlite:///./data/app.db"
    clerk_jwt_issuer: str = ""
    clerk_jwks_url: str = ""
    clerk_authorized_parties: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings loaded from environment variables."""
    return Settings()
