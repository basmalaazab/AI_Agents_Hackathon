"""
Application configuration loaded from environment variables.
Uses pydantic-settings for validation and type coercion.
"""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql://bi_user:bi_password@localhost:5432/bi_db"

    # Application
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # Mock API
    mock_api_url: str = "http://localhost:8001"

    # Scheduler
    scheduler_interval_minutes: int = 60

    # Optional integrations
    google_sheets_credentials_file: Optional[str] = None
    google_sheets_token_file: Optional[str] = None
    shopify_shop_name: Optional[str] = None
    shopify_access_token: Optional[str] = None

    # Person 3: AI Agent Settings
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    ai_agent_model: str = "built-in-analyst"
    ai_agent_temperature: float = 0.2

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

