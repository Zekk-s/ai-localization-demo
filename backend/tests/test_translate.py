"""Smoke tests for the mock provider and locale validation."""

from __future__ import annotations

import os

os.environ.setdefault("LOCALIZATION_PROVIDER", "mock")

from fastapi.testclient import TestClient

from app.main import app
from app.translate.engine import reset_engine_for_tests


def test_healthz():
    with TestClient(app) as client:
        r = client.get("/healthz")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


def test_locales_endpoint():
    with TestClient(app) as client:
        r = client.get("/v1/locales")
        assert r.status_code == 200
        data = r.json()
        codes = {loc["code"] for loc in data["locales"]}
        assert {"en", "tr", "no"}.issubset(codes)


def test_translate_mock():
    reset_engine_for_tests()
    with TestClient(app) as client:
        r = client.post(
            "/v1/translate",
            json={"text": "Hello", "source": "en", "target": "tr"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["provider"] == "mock"
        assert "[en->tr/" in body["text"]


def test_translate_with_glossary():
    reset_engine_for_tests()
    with TestClient(app) as client:
        r = client.post(
            "/v1/translate",
            json={
                "text": "world",
                "source": "en",
                "target": "tr",
                "glossary": {"world": "dünya"},
            },
        )
        assert r.status_code == 200
        assert r.json()["text"] == "dünya"


def test_translate_rejects_unknown_locale():
    with TestClient(app) as client:
        r = client.post(
            "/v1/translate",
            json={"text": "hi", "source": "xx", "target": "en"},
        )
        assert r.status_code == 400


def test_batch_translate():
    reset_engine_for_tests()
    with TestClient(app) as client:
        r = client.post(
            "/v1/translate/batch",
            json={
                "items": [
                    {"text": "Hello", "source": "en", "target": "tr"},
                    {"text": "World", "source": "en", "target": "tr"},
                ],
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert len(body["results"]) == 2