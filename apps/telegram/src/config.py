"""Telegram bot configuration."""
from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram
    TELEGRAM_BOT_TOKEN: str = Field(description="Telegram Bot API token from @BotFather")
    TELEGRAM_WEBHOOK_URL: str | None = None  # Set for production webhook mode

    # Allowlist — comma-separated Telegram user IDs (empty = allow all)
    TELEGRAM_ALLOWED_USERS: str = ""

    # Minoverse API
    MINOVERSE_API_URL: str = "http://localhost:8000"
    MINOVERSE_API_KEY: str | None = None

    # Defaults
    DEFAULT_INGEST_MODE: str = "technical"

    # Logging
    LOG_LEVEL: str = "info"

    @property
    def allowed_user_ids(self) -> set[int]:
        if not self.TELEGRAM_ALLOWED_USERS:
            return set()  # empty = allow all
        return {int(uid.strip()) for uid in self.TELEGRAM_ALLOWED_USERS.split(",") if uid.strip()}


settings = Settings()
