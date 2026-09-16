"""LLM provider abstraction.

Scientific integrity constraint: the LLM is used ONLY as an optional phrasing
assistant for conversational text (e.g. smoothing clarifying questions into
natural language). It never generates scientific claims, evidence, numeric
estimates, or citations — those come exclusively from the deterministic
reasoning engine (app/reasoning) and the evidence store (app/evidence). This
keeps the system's factual output correct even with no LLM configured at all
and prevents hallucinated citations regardless of provider.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import httpx

from app.core.config import Settings, get_settings


class LLMProvider(ABC):
    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str) -> str: ...

    @property
    @abstractmethod
    def name(self) -> str: ...


class MockDeterministicLLMProvider(LLMProvider):
    """Offline, deterministic fallback. Simply returns the templated prompt
    content unchanged (the reasoning/conversation modules already produce
    fully-formed natural language templates), so behaviour is fully
    reproducible without any external dependency.
    """

    @property
    def name(self) -> str:
        return "mock-deterministic"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        return user_prompt


class OpenAICompatibleLLMProvider(LLMProvider):
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = httpx.Client(
            base_url=settings.openai_base_url,
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            timeout=30.0,
        )

    @property
    def name(self) -> str:
        return f"openai:{self.settings.openai_chat_model}"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        try:
            resp = self._client.post(
                "/chat/completions",
                json={
                    "model": self.settings.openai_chat_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.2,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception:
            # Degrade gracefully: fall back to the deterministic template text
            # rather than failing the request when the provider is unreachable.
            return user_prompt


_provider: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    global _provider
    if _provider is not None:
        return _provider
    settings = get_settings()
    if settings.llm_provider == "openai" and settings.openai_api_key:
        _provider = OpenAICompatibleLLMProvider(settings)
    else:
        _provider = MockDeterministicLLMProvider()
    return _provider
