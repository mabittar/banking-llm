"""
Configuration module.

Loads environment variables from .env and exposes application settings.
"""

import os
from enum import Enum
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic_settings import SettingsConfigDict


class AppEnvironment(Enum):
    LOCAL = "local"
    DEVELOPMENT = "development"


class BaseSettings(PydanticBaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        extra="ignore",
    )

    TITLE: str = "LangChain LCEL API"
    DESCRIPTION: str = "A minimal LangChain LCEL chain exposed through FastAPI."
    IS_DEBUG: bool = False
    TIMEZONE: str = "America/Sao_Paulo"

    OPENROUTER_API_KEY: str = Field("", description="API key for OpenRouter.")
    OPENROUTER_BASE_URL: str = Field(
        "https://openrouter.ai/api/v1",
        description="Base URL for OpenRouter API.",
    )
    OPENROUTER_MODEL: str = Field(
        "google/gemini-2.5-flash",
        description="Model for OpenRouter API.",
    )

    OLLAMA_BASE_URL: str = Field(
        "http://localhost:11434",
        description="Base URL for Ollama API.",
    )
    OLLAMA_MODEL: str = Field(
        "qwen3.5:latest",
        description="Model for Ollama.",
    )

    # Banking
    CLIENT_ID: str = Field("", description="Client ID for banking.")
    REALM_NAME: str = Field("", description="Realm name for banking.")
    JWT_SECRET: str = Field("", description="JWT secret for banking.")
    BANKING_BASE_URL: str = Field("https://banking.example.com", description="Base URL for banking API.")

    # Cache
    REDIS_HOST: str = Field("localhost", description="Redis host.")
    REDIS_PORT: int = Field(6379, description="Redis port.")
    REDIS_PASSWORD: str | None = Field(None, description="Redis password. Use null for no auth.")

    @field_validator("REDIS_PASSWORD", mode="before")
    @classmethod
    def _parse_redis_password(cls, v: str | None) -> str | None:
        if v is None or v.lower() == "null" or v.strip() == "":
            return None
        return v

    @property
    def set_app_attributes(self) -> dict[str, str | bool | None]:
        return {
            "title": self.TITLE,
            "debug": self.IS_DEBUG,
            "description": self.DESCRIPTION,
        }


class AppDevelopmentSettings(BaseSettings):
    ENVIRONMENT: AppEnvironment = AppEnvironment.DEVELOPMENT
    DESCRIPTION: str = f"Application ({AppEnvironment.DEVELOPMENT})."
    IS_DEBUG: bool = False


class AppLocalSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: AppEnvironment = AppEnvironment.LOCAL
    DESCRIPTION: str = f"Application ({AppEnvironment.LOCAL})."
    IS_DEBUG: bool = True


class FactoryAppSettings:
    def __init__(self, environment: str):
        self.environment = environment

    def __call__(self) -> BaseSettings:
        if self.environment == AppEnvironment.DEVELOPMENT:
            return AppDevelopmentSettings()
        return AppLocalSettings()


@lru_cache
def get_settings() -> BaseSettings:
    """Get application settings."""
    env = os.getenv("APP_ENV", AppEnvironment.LOCAL)
    return FactoryAppSettings(env)()


settings = get_settings()
