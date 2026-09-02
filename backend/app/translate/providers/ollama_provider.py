"""Ollama local provider — fully self-hosted translation."""

from __future__ import annotations

from typing import AsyncIterator

import httpx


class OllamaTranslationError(RuntimeError):
    pass


class OllamaTranslationEngine:
    def __init__(self, settings) -> None:
        self.settings = settings
        self._client: httpx.AsyncClient | None = None

    def _client_lazy(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.settings.ollama_base_url,
                timeout=httpx.Timeout(60.0, connect=10.0),
            )
        return self._client

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
        glossary_text = ", ".join(f"{k}->{v}" for k, v in glossary.items()) or "(none)"
        prompt = (
            f"Translate from {source} to {target} with {formality} tone. "
            f"Glossary: {glossary_text}.\n\n{text}"
        )
        try:
            r = await client.post(
                "/api/generate",
                json={"model": self.settings.ollama_model, "prompt": prompt, "stream": False},
            )
            r.raise_for_status()
            data = r.json()
        except httpx.HTTPError as e:
            raise OllamaTranslationError(f"ollama http error: {e}") from e
        return {
            "text": data["response"].strip(),
            "source": source,
            "target": target,
            "provider": "ollama",
            "formality": formality,
            "tokens_in": len(text.split()),
            "tokens_out": len(data["response"].split()),
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