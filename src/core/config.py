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

    # LLM Options
    LLM_TEMPERATURE: float = Field(0.1, description="Temperature for LLM generation.")
    LLM_TOP_K: int = Field(40, description="Top-k sampling parameter.")
    LLM_TOP_P: float = Field(0.9, description="Top-p sampling parameter.")

    # Banking
    CLIENT_ID: str = Field("", description="Client ID for banking.")
    REALM_NAME: str = Field("", description="Realm name for banking.")
    AUDIENCE: str = Field("", description="Audience for banking.")
    JWT_SECRET: str = Field(
        "", description="JWT secret (JWK EC private key) for banking."
    )
    BANKING_BASE_URL: str = Field(
        "https://banking.example.com", description="Base URL for banking API."
    )
    FIN_ACCOUNT_ID: str = Field(
        "", description="Primary financial account ID for PIX operations."
    )
    FIN_ACCOUNT_ID_FALLBACK: str = Field(
        "", description="Fallback financial account ID for retry on failure."
    )
    TRANSACTION_HASH_SECRET: str = Field(
        "", description="Secret key for HMAC-SHA256 Transaction-Hash-Key generation."
    )

    # Guardrail
    GUARDRAIL_ENABLED: bool = Field(True, description="Enable/disable guardrail node.")
    GUARDRAIL_MODEL: str = Field(
        "meta-llama/llama-guard-4-12b",
        description="Model used for safeguard analysis.",
    )
    GUARDRAIL_THRESHOLD: float = Field(
        0.7,
        description="Score threshold above which input is blocked (0.0-1.0).",
    )

    # Cache
    REDIS_HOST: str = Field("localhost", description="Redis host.")
    REDIS_PORT: int = Field(6379, description="Redis port.")
    REDIS_PASSWORD: str | None = Field(
        None, description="Redis password. Use null for no auth."
    )

    # Database
    DBNAME: str = Field("banking-llm", description="PostgreSQL database name.")
    DB_USER: str = Field("postgres", description="PostgreSQL user.")
    DB_PASSWORD: str = Field("mysecretpassword", description="PostgreSQL password.")
    DB_HOST: str = Field("localhost", description="PostgreSQL host.")
    DB_PORT: int = Field(5432, description="PostgreSQL port.")

    # Observability (OpenTelemetry). All signals are no-op while OTEL_ENABLED is false.
    OTEL_ENABLED: bool = Field(
        False, description="Master switch for all telemetry. No-op when false."
    )
    OTEL_SERVICE_NAME: str = Field(
        "langchain-pix-environment",
        description="service.name reported in the Resource.",
    )
    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field(
        "http://otel-collector:4317", description="OTLP endpoint of the Collector."
    )
    OTEL_EXPORTER_OTLP_PROTOCOL: str = Field(
        "grpc", description="OTLP transport: 'grpc' or 'http/protobuf'."
    )
    OTEL_TRACES_SAMPLER_ARG: float = Field(
        1.0, description="Trace sampling ratio (1.0 = 100%, suited for dev)."
    )
    OTEL_METRICS_ENABLED: bool = Field(
        True, description="Enable the metrics pipeline when telemetry is on."
    )
    OTEL_LOGS_EXPORT_ENABLED: bool = Field(
        True, description="Enable OTLP log export when telemetry is on."
    )
    GRAFANA_MCP_ENABLED: bool = Field(
        False, description="Enable the optional Grafana MCP service."
    )
    GRAFANA_URL: str = Field(
        "http://grafana:3000", description="Grafana URL consumed by the MCP server."
    )
    GRAFANA_SERVICE_ACCOUNT_TOKEN: str = Field(
        "", description="Read-only (Viewer) Grafana service account token for the MCP."
    )

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

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DBNAME}?sslmode=disable"


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
