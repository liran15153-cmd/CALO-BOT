from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./data/app.db"
    backend_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"
    anthropic_api_key: str | None = Field(default=None, repr=False)
    anthropic_model: str = "claude-haiku-4-5"

    model_config = SettingsConfigDict(
        env_file=(".env.local", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    @property
    def ai_provider_status(self) -> str:
        return "configured" if self.anthropic_api_key else "not_configured"


@lru_cache
def get_settings() -> Settings:
    return Settings()
