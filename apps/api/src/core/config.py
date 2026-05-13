"""Application configuration loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://minoverse:minoverse@localhost:5432/minoverse"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Vault
    vault_path: str = "../../vault"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    # AI provider selection: "gemini" | "ollama" | "lmstudio"
    ai_provider: str = "gemini"

    # Ollama (used when ai_provider = "ollama")
    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "bge-m3"
    chat_model: str = "qwen3:0.6b"

    # Gemini (used when ai_provider = "gemini")
    # Comma-separated list of API keys for round-robin rotation
    gemini_api_keys: str = ""
    # Optional: path to a Google service-account JSON file.
    # When set, takes precedence over gemini_api_keys.
    gemini_service_account_path: str = ""
    # Google Cloud project (required with service account auth)
    gemini_project_id: str = ""
    # Vertex AI region (service-account auth only)
    gemini_location: str = "us-central1"
    # Physical model names
    gemini_chat_model: str = "gemini-2.0-flash"
    gemini_embedding_model: str = "text-embedding-004"

    # LM Studio (used when ai_provider = "lmstudio")
    lmstudio_base_url: str = "http://localhost:1234"
    lmstudio_api_key: str = ""
    lmstudio_chat_model: str = ""
    lmstudio_embedding_model: str = ""

    # AutoIngest services
    scraping_service_url: str = "http://localhost:8001"

    def parsed_gemini_api_keys(self) -> list[str]:
        """Return the list of Gemini API keys parsed from the comma-separated setting."""
        return [k.strip() for k in self.gemini_api_keys.split(",") if k.strip()]


settings = Settings()
