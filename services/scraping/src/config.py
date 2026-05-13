"""Scraping service configuration."""
from __future__ import annotations

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Service
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8001
    LOG_LEVEL: str = "info"
    DEBUG: bool = False

    # Playwright
    PLAYWRIGHT_TIMEOUT_MS: int = 15000
    PLAYWRIGHT_HEADLESS: bool = True
    PLAYWRIGHT_MAX_CONCURRENT: int = 3

    # Rate limiting
    SCRAPE_DELAY_MS: int = 1000
    MAX_RETRIES: int = 3

    # Queue
    REDIS_URL: str = "redis://localhost:6379/0"
    NATS_URL: str = "nats://localhost:4222"
    USE_NATS: bool = False

    # GitHub
    GITHUB_TOKEN: str | None = Field(default=None)

    # Content limits
    MAX_CONTENT_BYTES: int = 10 * 1024 * 1024  # 10MB
    MAX_VIDEO_DURATION_SECONDS: int = 3600  # 1h


settings = Settings()
