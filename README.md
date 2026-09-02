# ai-localization-demo

Real-time AI-powered translation and localization demo.

A minimal, provider-agnostic FastAPI service that translates and adapts text across
languages with locale-aware tone, formality, and terminology hints. The repo doubles as
a working reference for integrating large-language-model localization into production
products without leaking prompts or contracts into the client bundle.

## Features

- **Provider-agnostic backend** — swap between OpenAI, Anthropic, local models, or
  mocks via environment variables; no provider lock-in in the request path.
- **Locale-aware prompting** — per-locale terminology glossary, formality level,
  and tone controls (`formality: formal | neutral | casual`).
- **Streaming endpoint** — Server-Sent Events translation for live UI updates.
- **Type-safe client SDK** — TypeScript client generated from the OpenAPI schema.
- **Demo frontend** — minimal Vite page that streams translations while typing.
- **Observability by default** — structured logs, request IDs, latency metrics on
  `/metrics` (Prometheus exposition format).

## Quick start

```bash
# 1. Backend
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
# Edit .env with your provider credentials (never commit)
uvicorn app.main:app --reload --port 8000

# 2. Frontend
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

## API

| Method | Path                       | Description                          |
| ------ | -------------------------- | ------------------------------------ |
| GET    | `/healthz`                 | Liveness probe                       |
| GET    | `/v1/locales`              | Supported locale codes               |
| POST   | `/v1/translate`            | Single-shot translation              |
| POST   | `/v1/translate/stream`     | SSE streaming translation            |
| POST   | `/v1/translate/batch`      | Bulk translation up to 100 items     |
| GET    | `/metrics`                 | Prometheus metrics                   |

`POST /v1/translate`

```json
{
  "text": "Hello, world.",
  "source": "en",
  "target": "tr",
  "formality": "neutral",
  "glossary": { "world": "dünya" }
}
```

## Architecture

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Frontend    │─────▶│   FastAPI    │─────▶│   Provider   │
│  (Vite/TS)   │ SSE  │   Backend    │ HTTP │ (OpenAI/etc) │
└──────────────┘      └──────────────┘      └──────────────┘
                             │
                             ▼
                      ┌──────────────┐
                      │   Glossary   │
                      │   Cache      │
                      │   Logs       │
                      └──────────────┘
```

## Security

- API keys live in `.env` (gitignored). `.env.example` ships with placeholders only.
- No provider credentials reach the frontend bundle.
- Rate-limit middleware (`slowapi`) caps per-IP requests.
- PII redaction hook ready for production (`app/redaction.py`).

## Roadmap

- [ ] Provider-agnostic retry/backoff (currently: per-provider)
- [ ] Per-tenant glossary isolation
- [ ] Cost telemetry per request
- [ ] Locale-aware MT-hybrid fallback (DeepL + LLM)

## License

MIT — see `LICENSE`.

## Maintainer

[@Zekiog](https://github.com/Zekiog) · part of [@Zekk-s](https://github.com/Zekk-s).