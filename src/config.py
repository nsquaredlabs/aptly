from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Required
    supabase_url: str
    supabase_service_key: str
    redis_url: str
    aptly_admin_secret: str

    # Optional with defaults
    environment: str = "development"
    log_level: str = "info"
    port: int = 8000
    sentry_dsn: str | None = None

    # Rate limits by plan
    rate_limit_free: int = 100
    rate_limit_pro: int = 1000
    rate_limit_enterprise: int = 10000

    # API version
    api_version: str = "1.0.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
