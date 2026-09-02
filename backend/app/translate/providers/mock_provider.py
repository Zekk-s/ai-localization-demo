"""Deterministic mock provider — used for tests and local dev without credentials."""

from __future__ import annotations

from typing import AsyncIterator


class MockTranslationEngine:
    def __init__(self, settings) -> None:
        self.settings = settings

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
        # Apply glossary: prefer glossary over raw text where terms match.
        out = text
        for src_term, tgt_term in glossary.items():
            out = out.replace(src_term, tgt_term)

        # Deterministic mock — tag the locale pair so tests can assert against it.
        if out == text:
            out = f"[{source}->{target}/{formality}] {text}"

        return {
            "text": out,
            "source": source,
            "target": target,
            "provider": "mock",
            "formality": formality,
            "tokens_in": len(text.split()),
            "tokens_out": len(out.split()),
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