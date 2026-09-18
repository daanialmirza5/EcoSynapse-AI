"""Application configuration loaded from environment variables.

Every external dependency (AI provider, embedding provider, database) is optional
at startup: the app must boot and serve the deterministic demo experience even
when no API keys are configured. See app/ai/llm.py and app/ai/embeddings.py for
the fallback logic.
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

    # Explicit override for where data/seed/*.json lives. Leave unset for a
    # local monorepo checkout (path is derived relative to this file); set
    # this in Docker images that copy the seed data to a fixed location
    # (see apps/api/Dockerfile).
    seed_data_dir: str | None = None

    max_request_body_bytes: int = 2_000_000
    # Basic in-memory, single-process rate limit (see app/main.py::InMemoryRateLimiter
    # for why this doesn't scale across multiple instances). 0 disables it.
    rate_limit_per_minute: int = 120

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def resolved_database_url(self) -> str:
        """Normalizes managed-Postgres URLs (Railway, Heroku, etc. commonly
        hand out a bare ``postgresql://`` or legacy ``postgres://`` URL) to
        the ``postgresql+psycopg://`` driver this app installs, so pasting a
        platform-provided connection string just works without manual
        editing."""
        url = self.database_url
        if url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url[len("postgres://") :]
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://") :]
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
