"""Health and locale-list endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.locales import SUPPORTED_LOCALES

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/v1/locales")
async def list_locales() -> dict[str, list[dict[str, str]]]:
    return {
        "locales": [
            {"code": loc.code, "name": loc.name, "formality_default": loc.formality_default}
            for loc in SUPPORTED_LOCALES.values()
        ],
    }