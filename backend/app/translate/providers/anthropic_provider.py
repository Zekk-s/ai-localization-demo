"""Anthropic Messages API provider."""

from __future__ import annotations

from typing import AsyncIterator

import httpx


class AnthropicTranslationError(RuntimeError):
    pass


class AnthropicTranslationEngine:
    def __init__(self, settings) -> None:
        self.settings = settings
        self._client: httpx.AsyncClient | None = None

    def _client_lazy(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url="https://api.anthropic.com/v1",
                headers={
                    "x-api-key": self.settings.anthropic_api_key or "",
                    "anthropic-version": "2023-06-01",
                },
                timeout=httpx.Timeout(30.0, connect=10.0),
            )
        return self._client

    def _system_prompt(self, *, source: str, target: str, formality: str, glossary: dict[str, str]) -> str:
        glossary_text = (
            "\n".join(f"- {k} -> {v}" for k, v in glossary.items()) if glossary else "(none)"
        )
        return (
            f"Precise translator. {source} -> {target}, {formality} tone. "
            f"Use the glossary verbatim.\n\nGlossary:\n{glossary_text}"
        )

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
        client = self._client_lazy()
        payload = {
            "model": self.settings.anthropic_model,
            "max_tokens": 1024,
            "system": self._system_prompt(
                source=source, target=target, formality=formality, glossary=glossary
            ),
            "messages": [{"role": "user", "content": text}],
        }
        try:
            r = await client.post("/messages", json=payload)
            r.raise_for_status()
            data = r.json()
        except httpx.HTTPError as e:
            raise AnthropicTranslationError(f"anthropic http error: {e}") from e
        return {
            "text": data["content"][0]["text"].strip(),
            "source": source,
            "target": target,
            "provider": "anthropic",
            "formality": formality,
            "tokens_in": data["usage"]["input_tokens"],
            "tokens_out": data["usage"]["output_tokens"],
        }

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
        # Anthropic SSE streaming would be wired here. Same shape as OpenAI.
        result = await self.translate(
            text=text,
            source=source,
            target=target,
            formality=formality,
            glossary=glossary,
            request_id=request_id,
        )
        for token in result["text"].split(" "):
            yield token + " "