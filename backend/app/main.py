"""FastAPI entry point for ai-localization-demo.

Wires routers, middleware, and observability. All public routes live under /v1/*.
"""

from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.responses import Response

from app.config import settings
from app.locales import SUPPORTED_LOCALES
from app.routers import health, translate

app = FastAPI(
    title="ai-localization-demo",
    version=os.environ.get("APP_VERSION", "0.1.0"),
    description="Provider-agnostic AI translation reference.",
)

# CORS — strict by default; env-configured origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Rate limiting
app.state.limiter = settings.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Attach a request ID to every request and response."""
    import uuid

    rid = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = rid
    response = await call_next(request)
    response.headers["x-request-id"] = rid
    return response


app.include_router(health.router)
app.include_router(translate.router, prefix="/v1")


@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> Response:
    """Return a stable error envelope; never leak stack traces in prod."""
    if settings.log_level == "debug":
        return JSONResponse(
            status_code=500,
            content={"error": "internal", "detail": str(exc)},
        )
    return JSONResponse(status_code=500, content={"error": "internal"})


@app.get("/")
async def root() -> dict[str, object]:
    return {
        "service": "ai-localization-demo",
        "version": app.version,
        "provider": settings.provider,
        "locales": list(SUPPORTED_LOCALES.keys()),
    }