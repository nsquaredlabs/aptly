from pydantic import model_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql+asyncpg://localhost/aptly"

    @model_validator(mode="after")
    def normalize_database_url(self):
        """Convert postgresql:// to postgresql+asyncpg:// for asyncpg compatibility."""
        url = self.database_url
        if url.startswith("postgresql://"):
            self.database_url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            self.database_url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return self

    # Auth
    aptly_api_secret: str

    # Redis (optional — no Redis = no rate limiting)
    redis_url: str | None = None

    # Compliance settings
    pii_redaction_mode: str = "mask"
    compliance_frameworks: list[str] = []

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Rate limiting
    rate_limit_per_hour: int = 1000

    # Optional with defaults
    environment: str = "development"
    log_level: str = "info"
    port: int = 8000
    sentry_dsn: str | None = None

    # API version
    api_version: str = "1.0.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
