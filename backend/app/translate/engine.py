"""Provider-agnostic translation engine.

The engine returns a dict compatible with `TranslateResponse` and never raises for
provider-level errors — those are caught, logged, and re-raised as `RuntimeError`.
"""

from __future__ import annotations

from typing import AsyncIterator, Protocol

from app.config import settings


class TranslationEngine(Protocol):
    async def translate(
        self,
        *,
        text: str,
        source: str,
        target: str,
        formality: str,
        glossary: dict[str, str],
        request_id: str | None,
    ) -> dict:
        ...

    async def translate_stream(
        self,
        *,
        text: str,
        source: str,
        target: str,
        formality: str,
        glossary: dict[str, str],
        request_id: str | None,
    ) -> AsyncIterator[str]:
        ...


_cached_engine: TranslationEngine | None = None


def get_engine() -> TranslationEngine:
    """Lazy, cached singleton — provider chosen from settings at first call."""
    global _cached_engine
    if _cached_engine is not None:
        return _cached_engine

    provider = settings.provider
    if provider == "openai":
        from app.translate.providers.openai_provider import OpenAITranslationEngine

        _cached_engine = OpenAITranslationEngine(settings)
    elif provider == "anthropic":
        from app.translate.providers.anthropic_provider import AnthropicTranslationEngine

        _cached_engine = AnthropicTranslationEngine(settings)
    elif provider == "ollama":
        from app.translate.providers.ollama_provider import OllamaTranslationEngine

        _cached_engine = OllamaTranslationEngine(settings)
    else:
        from app.translate.providers.mock_provider import MockTranslationEngine

        _cached_engine = MockTranslationEngine(settings)

    return _cached_engine


def reset_engine_for_tests() -> None:
    """Drop the cached engine — call between tests that change provider."""
    global _cached_engine
    _cached_engine = None