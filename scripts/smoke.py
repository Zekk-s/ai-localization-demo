#!/usr/bin/env python
"""Smoke test against a running uvicorn instance.

Usage:
    python scripts/smoke.py
"""

from __future__ import annotations

import os
import sys

import httpx

BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost:8000")


def main() -> int:
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        r = client.get("/healthz")
        r.raise_for_status()
        print("OK /healthz")

        r = client.get("/v1/locales")
        r.raise_for_status()
        print(f"OK /v1/locales ({len(r.json()['locales'])} locales)")

        r = client.post(
            "/v1/translate",
            json={"text": "Hello", "source": "en", "target": "tr"},
        )
        r.raise_for_status()
        print(f"OK /v1/translate -> {r.json()['text']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())