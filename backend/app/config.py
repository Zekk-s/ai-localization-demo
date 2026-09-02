"""Settings loaded from environment variables.

Never hard-code credentials. Provide `.env.example` instead and copy to `.env` for
local development.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from slowapi import Limiter
from slowapi.util import get_remote_address


ProviderName = Literal["openai", "anthropic", "ollama", "mock"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Provider selection
    localization_provider: ProviderName = Field(default="mock", alias="LOCALIZATION_PROVIDER")

    # OpenAI
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")

    # Anthropic
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-5-haiku-latest", alias="ANTHROPIC_MODEL")

    # Ollama
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3.1:8b", alias="OLLAMA_MODEL")

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    log_level: str = Field(default="info", alias="LOG_LEVEL")
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"],
        alias="CORS_ORIGINS",
    )

    # Rate limit (per-IP per-minute)
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")

    @property
    def provider(self) -> ProviderName:
        return self.localization_provider

    @property
    def limiter(self) -> Limiter:
        return Limiter(
            key_func=get_remote_address,
            default_limits=[f"{self.rate_limit_per_minute}/minute"],
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()