from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./data/app.db"
    backend_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"
    anthropic_api_key: str | None = Field(default=None, repr=False)
    anthropic_model: str = "claude-haiku-4-5"
    anthropic_chat_model: str | None = None
    daily_ai_token_limit: int = Field(default=50000, ge=0)
    language_guard_enabled: bool = True
    language_guard_mode: str = Field(default="repair", pattern="^(off|repair|strict)$")
    supabase_url: str | None = None
    supabase_publishable_key: str | None = Field(default=None, repr=False)
    supabase_secret_key: str | None = Field(default=None, repr=False)
    supabase_jwks_url: str | None = None
    supabase_auth_required: bool = False
    supabase_storage_bucket: str = "meal-images"

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

    @property
    def chat_model(self) -> str:
        return self.anthropic_chat_model or self.anthropic_model

    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_publishable_key)

    @property
    def supabase_auth_status(self) -> str:
        if not self.supabase_configured:
            return "not_configured"
        return "required" if self.supabase_auth_required else "configured_optional"

    @property
    def supabase_storage_status(self) -> str:
        if not self.supabase_configured:
            return "local"
        return "configured" if self.supabase_storage_bucket else "not_configured"


@lru_cache
def get_settings() -> Settings:
    return Settings()
