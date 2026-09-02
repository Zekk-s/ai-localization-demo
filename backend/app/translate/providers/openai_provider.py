"""OpenAI provider — uses Chat Completions streaming when streaming is requested."""

from __future__ import annotations

from typing import AsyncIterator

import httpx


class OpenAITranslationError(RuntimeError):
    pass


class OpenAITranslationEngine:
    def __init__(self, settings) -> None:
        self.settings = settings
        self._client: httpx.AsyncClient | None = None

    def _client_lazy(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.settings.openai_base_url,
                headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                timeout=httpx.Timeout(30.0, connect=10.0),
            )
        return self._client

    def _build_messages(
        self, *, text: str, source: str, target: str, formality: str, glossary: dict[str, str]
    ) -> list[dict]:
        glossary_text = (
            "\n".join(f"- {k} -> {v}" for k, v in glossary.items()) if glossary else "(none)"
        )
        system = (
            f"You are a precise translator. Translate from {source} to {target} with "
            f"{formality} tone. Use the supplied glossary exactly. Do not paraphrase terms "
            f"listed in the glossary.\n\nGlossary:\n{glossary_text}\n"
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ]

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
            "model": self.settings.openai_model,
            "messages": self._build_messages(
                text=text, source=source, target=target, formality=formality, glossary=glossary
            ),
            "temperature": 0.2,
        }
        try:
            r = await client.post("/chat/completions", json=payload)
            r.raise_for_status()
            data = r.json()
        except httpx.HTTPError as e:
            raise OpenAITranslationError(f"openai http error: {e}") from e
        return {
            "text": data["choices"][0]["message"]["content"].strip(),
            "source": source,
            "target": target,
            "provider": "openai",
            "formality": formality,
            "tokens_in": data["usage"]["prompt_tokens"],
            "tokens_out": data["usage"]["completion_tokens"],
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
        client = self._client_lazy()
        payload = {
            "model": self.settings.openai_model,
            "messages": self._build_messages(
                text=text, source=source, target=target, formality=formality, glossary=glossary
            ),
            "temperature": 0.2,
            "stream": True,
        }
        try:
            async with client.stream("POST", "/chat/completions", json=payload) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line.removeprefix("data: ").strip()
                    if data == "[DONE]":
                        break
                    import json

                    chunk = json.loads(data)
                    delta = chunk["choices"][0]["delta"].get("content")
                    if delta:
                        yield delta
        except httpx.HTTPError as e:
            raise OpenAITranslationError(f"openai stream error: {e}") from e