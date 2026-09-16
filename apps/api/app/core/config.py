"""Application configuration loaded from environment variables.

Every external dependency (AI provider, embedding provider, database) is optional
at startup: the app must boot and serve the deterministic demo experience even
when no API keys are configured. See app/ai/providers.py for the fallback logic.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "EcoSynapse AI"
    environment: str = "development"
    api_prefix: str = "/api/v1"

    # Database. Defaults to a local SQLite file so the project runs with zero
    # external services. Set DATABASE_URL to a postgresql+psycopg:// URL in
    # production (pgvector extension recommended, see docs/database-schema.md).
    database_url: str = "sqlite:///./ecosynapse.db"

    # CORS
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # AI / LLM provider. "mock" is a deterministic, offline, rule-based
    # provider used for natural-language *parsing assistance* only. It never
    # invents scientific facts. Set to "openai" to use an OpenAI-compatible
    # chat completions endpoint for phrasing assistance (still constrained by
    # the deterministic reasoning engine for all factual content).
    llm_provider: Literal["mock", "openai"] = "mock"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_chat_model: str = "gpt-4o-mini"

    # Embedding provider. "hashing" is a deterministic, offline TF-IDF-style
    # hashing embedding requiring no network access or API key. Set to
    # "openai" to use an OpenAI-compatible embeddings endpoint.
    embedding_provider: Literal["hashing", "openai"] = "hashing"
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 256

    app_secret: str = "dev-secret-change-me"

    max_request_body_bytes: int = 2_000_000

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
