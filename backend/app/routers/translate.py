"""Translation endpoints — single-shot, streaming (SSE), and batch."""

from __future__ import annotations

import json
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.locales import SUPPORTED_LOCALES, is_supported
from app.translate.engine import TranslationEngine, get_engine

router = APIRouter(prefix="/translate", tags=["translate"])


class TranslateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    source: str = Field(min_length=2, max_length=5)
    target: str = Field(min_length=2, max_length=5)
    formality: str = Field(default="neutral", pattern="^(formal|neutral|casual)$")
    glossary: dict[str, str] = Field(default_factory=dict)


class TranslateResponse(BaseModel):
    text: str
    source: str
    target: str
    provider: str
    formality: str
    tokens_in: int
    tokens_out: int


@router.post("", response_model=TranslateResponse)
async def translate(req: TranslateRequest, request: Request) -> TranslateResponse:
    if not is_supported(req.source):
        raise HTTPException(400, f"unsupported source locale: {req.source}")
    if not is_supported(req.target):
        raise HTTPException(400, f"unsupported target locale: {req.target}")

    engine = get_engine()
    result = await engine.translate(
        text=req.text,
        source=req.source,
        target=req.target,
        formality=req.formality,
        glossary=req.glossary,
        request_id=getattr(request.state, "request_id", None),
    )
    return TranslateResponse(**result)


@router.post("/stream")
async def translate_stream(req: TranslateRequest, request: Request):
    if not is_supported(req.source) or not is_supported(req.target):
        raise HTTPException(400, "unsupported locale")

    engine = get_engine()
    rid = getattr(request.state, "request_id", None)

    async def event_source() -> AsyncIterator[dict]:
        async for chunk in engine.translate_stream(
            text=req.text,
            source=req.source,
            target=req.target,
            formality=req.formality,
            glossary=req.glossary,
            request_id=rid,
        ):
            yield {"event": "token", "data": json.dumps({"delta": chunk})}
        yield {"event": "done", "data": json.dumps({"ok": True})}

    return EventSourceResponse(event_source())


class BatchTranslateRequest(BaseModel):
    items: list[TranslateRequest] = Field(min_length=1, max_length=100)


class BatchTranslateResponse(BaseModel):
    results: list[TranslateResponse]


@router.post("/batch", response_model=BatchTranslateResponse)
async def translate_batch(req: BatchTranslateRequest, request: Request) -> BatchTranslateResponse:
    engine = get_engine()
    rid = getattr(request.state, "request_id", None)
    results: list[TranslateResponse] = []
    for item in req.items:
        if not is_supported(item.source) or not is_supported(item.target):
            raise HTTPException(400, f"unsupported locale in batch: {item.source}->{item.target}")
        result = await engine.translate(
            text=item.text,
            source=item.source,
            target=item.target,
            formality=item.formality,
            glossary=item.glossary,
            request_id=rid,
        )
        results.append(TranslateResponse(**result))
    return BatchTranslateResponse(results=results)


# Re-export for type checkers
_ = (TranslationEngine,)