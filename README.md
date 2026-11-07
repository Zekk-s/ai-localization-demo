# ai-localization-demo

A FastAPI app and a small Vite page. The default provider is `mock`, which rewrites the input in process and does not call a model. The page loads the locale list, and on submit it posts one translation and shows the `text` field from the response.

## Run

`uvicorn app.main:app` imports the package `app`, which lives in `backend/app`. Run it with `backend/` as the working directory. From the repository root the same command fails with `ModuleNotFoundError: No module named 'app'`.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn app.main:app --reload --port 8000
```

A `.env` file is optional. With no `.env`, `LOCALIZATION_PROVIDER` is `mock`. If you copy the example, put it in the uvicorn working directory (`backend/.env`). `backend/app/config.py` reads `.env` from the process working directory.

```bash
cd frontend
npm install
npm run dev
```

`frontend/vite.config.ts` serves the page on port 5173 and proxies `/v1` and `/healthz` to `http://localhost:8000`. Open http://localhost:5173. The proxy does not forward `/`, `/metrics`, `/docs`, or `/openapi.json`.

`python scripts/smoke.py` calls `GET /healthz`, `GET /v1/locales`, and `POST /v1/translate` on `SMOKE_BASE_URL` (default `http://localhost:8000`). Start the API first. The script imports `httpx`, which is pinned in `backend/requirements.txt`.

## What the page does

`frontend/src/App.tsx` is one form: source, target, formality, and text. The initial text is `Hello, world.`, source `en`, target `tr`, formality `neutral`. On load it fetches `GET /v1/locales` and fills the two selects. Submit sends:

```json
{
  "text": "Hello, world.",
  "source": "en",
  "target": "tr",
  "formality": "neutral",
  "glossary": {}
}
```

With the mock provider the response `text` is `[en->tr/neutral] Hello, world.` The page prints that string. It calls `POST /v1/translate` once per submit. The stream route is unused by the page.

`frontend/package.json` scripts are `dev` (`vite`), `build` (`tsc -b && vite build`), `preview` (`vite preview`), `lint` (`eslint . --ext ts,tsx`), and `test` (`vitest`). Runtime dependencies are `react` and `react-dom`. The package is private and version `0.1.0`.

## Layout

```text
.env.example
.gitignore
AGENTS.md
LICENSE
README.md
backend/requirements.txt
backend/app/__init__.py
backend/app/config.py
backend/app/locales.py
backend/app/main.py
backend/app/routers/__init__.py
backend/app/routers/health.py
backend/app/routers/translate.py
backend/app/translate/__init__.py
backend/app/translate/engine.py
backend/app/translate/providers/__init__.py
backend/app/translate/providers/mock_provider.py
backend/app/translate/providers/openai_provider.py
backend/app/translate/providers/anthropic_provider.py
backend/app/translate/providers/ollama_provider.py
backend/tests/__init__.py
backend/tests/test_translate.py
frontend/index.html
frontend/package.json
frontend/tsconfig.json
frontend/vite.config.ts
frontend/src/App.tsx
frontend/src/main.tsx
frontend/src/styles.css
scripts/smoke.py
.github/CODEOWNERS
.github/ISSUE_TEMPLATE/bug_report.yml
.github/ISSUE_TEMPLATE/feature_request.yml
.github/PULL_REQUEST_TEMPLATE.md
.github/workflows/ci.yml
```

`backend/app/__init__.py` sets `__version__ = "0.1.0"`. `backend/app/translate/__init__.py` re-exports `TranslationEngine` and `get_engine`. The other `__init__.py` files mark the packages.

## Routes

Defined in `backend/app/main.py`, `backend/app/routers/health.py`, and `backend/app/routers/translate.py`. FastAPI also serves its built-in `/docs`, `/redoc`, and `/openapi.json`. `/metrics` is excluded from the schema.

| Method | Path | Response |
| --- | --- | --- |
| GET | `/` | `service`, `version`, `provider`, `locales` |
| GET | `/healthz` | `{"status": "ok"}` |
| GET | `/v1/locales` | `code`, `name`, `formality_default` for each locale |
| POST | `/v1/translate` | one translation |
| POST | `/v1/translate/stream` | SSE events `token` then `done` |
| POST | `/v1/translate/batch` | `items` translated in order |
| GET | `/metrics` | `prometheus_client.generate_latest()` |

`POST /v1/translate` body, as modeled in `TranslateRequest`:

```json
{
  "text": "Hello, world.",
  "source": "en",
  "target": "tr",
  "formality": "neutral",
  "glossary": { "world": "dünya" }
}
```

`text` is 1 to 8000 characters. `source` and `target` are 2 to 5 characters and must be keys of `SUPPORTED_LOCALES` in `backend/app/locales.py`. Anything else returns HTTP 400. `formality` is `formal`, `neutral`, or `casual`, default `neutral`. `glossary` is a string-to-string object, default `{}`.

The JSON result fields are `text`, `source`, `target`, `provider`, `formality`, `tokens_in`, and `tokens_out`.

Locale codes and `formality_default`:

| Code | Name | formality_default |
| --- | --- | --- |
| en | English | neutral |
| tr | Turkish | neutral |
| no | Norwegian | neutral |
| sv | Swedish | neutral |
| da | Danish | neutral |
| de | German | formal |
| ar | Arabic | formal |
| es | Spanish | neutral |
| fr | French | formal |

Translate handlers use the request's `formality`. They do not copy `formality_default` from the locale.

Batch requests take `items`, length 1 to 100. Each item has the same shape as a single translate body. The handler walks the list in order and returns `results`. An unknown locale returns HTTP 400.

The stream route returns `text/event-stream`. Each chunk is an event named `token` with data `{"delta": "<chunk>"}`. The last event is `done` with data `{"ok": true}`.

An HTTP middleware sets `x-request-id` on the response. It keeps the incoming header when the client sent one, and otherwise uses a UUID. The translate handlers pass that value into the engine. The provider functions accept `request_id` and do not read it.

`GET /metrics` writes the default `prometheus_client` registry. On a local import that registry contained process metrics, GC counters, and `python_info`. The app creates no `Counter`, `Histogram`, or `Gauge` of its own. `structlog` is listed in `backend/requirements.txt` and is not imported, so the app writes no log line of `request_id`, `latency_ms`, `tokens_in`, or `tokens_out`.

Unhandled exceptions return `{"error": "internal"}`. When `LOG_LEVEL` is `debug`, the body also includes `detail` with `str(exc)`. The handler does not attach a traceback.

`slowapi` is installed as middleware. The limiter key is the client address, and the default limit is `RATE_LIMIT_PER_MINUTE` (60) requests per minute. A local `TestClient` loop got HTTP 200 for 60 `GET /healthz` calls and HTTP 429 after that, with body `{"error":"Rate limit exceeded: 60 per 1 minute"}`.

CORS allows the origins in `CORS_ORIGINS` (default `http://localhost:5173`), methods `GET` and `POST`, and `allow_credentials` false.

`GET /` reports `version` from the environment variable `APP_VERSION`, or `0.1.0` when that variable is unset. `APP_VERSION` is not a field on `Settings` and is not listed in `.env.example`.

The OpenAPI info description string, set in `backend/app/main.py`, is `Translation HTTP API. Default provider is mock.`

## Providers

`get_engine()` in `backend/app/translate/engine.py` reads `settings.provider` once and caches the object. `reset_engine_for_tests()` clears the cache. The tests call it.

| `LOCALIZATION_PROVIDER` | Module | Behavior in this tree |
| --- | --- | --- |
| `mock` (default) | `mock_provider.py` | No HTTP. Replaces each glossary key with its value. If that changes the string, the result is the replaced text. If it does not, the result is `[source->target/formality] ` plus the original text. `tokens_in` and `tokens_out` are word counts. The stream method splits that finished string on spaces. |
| `openai` | `openai_provider.py` | `POST {OPENAI_BASE_URL}/chat/completions` with `httpx`. The prompt includes `source`, `target`, `formality`, and the glossary pairs. The stream method sends `"stream": true` and yields content deltas. The non-stream method reads `usage.prompt_tokens` and `usage.completion_tokens`. |
| `anthropic` | `anthropic_provider.py` | `POST https://api.anthropic.com/v1/messages` with header `anthropic-version: 2023-06-01`. `translate_stream` calls the non-stream method, then yields the text split on spaces. A comment in that method says Anthropic SSE streaming would be wired there. |
| `ollama` | `ollama_provider.py` | `POST {OLLAMA_BASE_URL}/api/generate` with `"stream": false`. The stream method calls that and yields the text split on spaces. Token counts are word counts. |

Glossary data is the object on the request. The mock provider does substring replacement. The other three interpolate the pairs into the prompt. There is no glossary file or cache.

For the example body above, the mock provider returns `Hello, dünya.` The glossary replacement changes the string, so the `[en->tr/neutral]` prefix is not added.

`OPENAI_API_KEY` is sent as `Authorization: Bearer <key>` and can be `None` if it was never set. `ANTHROPIC_API_KEY` is sent as `x-api-key`, using an empty string when unset. The app does not check that a key is present before the HTTP call.

## Dependencies

`backend/requirements.txt` pins:

- `fastapi==0.115.4`
- `uvicorn[standard]==0.32.0`
- `pydantic==2.9.2`
- `pydantic-settings==2.6.1`
- `python-dotenv==1.0.1`
- `httpx==0.27.2`
- `sse-starlette==2.1.3`
- `slowapi==0.1.9`
- `prometheus-client==0.21.0`
- `structlog==24.4.0`
- `pytest==8.3.3`
- `pytest-cov==6.0.0`
- `pytest-asyncio==0.24.0`
- `ruff==0.7.2`

Application modules import FastAPI, Pydantic, pydantic-settings, httpx, sse-starlette, slowapi, and prometheus-client. `python-dotenv` is not imported by name; pydantic-settings uses it to parse `.env`. `structlog` is not imported. The tests do not import `pytest-asyncio`.

Frontend devDependencies in `package.json` are `@types/react`, `@types/react-dom`, `@typescript-eslint/eslint-plugin`, `@typescript-eslint/parser`, `@vitejs/plugin-react`, `eslint`, `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`, `typescript`, `vite`, and `vitest`. There is no generated TypeScript client and no OpenAPI codegen script.

## Tests and CI

From `backend/`, the tests that exist are `backend/tests/test_translate.py`:

- `GET /healthz`
- `GET /v1/locales` includes `en`, `tr`, and `no`
- mock `POST /v1/translate` for `Hello` / `en` / `tr` returns a `text` containing `[en->tr/`
- glossary `{"world": "dünya"}` on text `world` returns `dünya`
- locale `xx` returns HTTP 400
- a two-item `POST /v1/translate/batch` returns two results

They set `LOCALIZATION_PROVIDER` to `mock` if it is unset. They do not call OpenAI, Anthropic, Ollama, `/v1/translate/stream`, or `/metrics`.

```bash
cd backend
pytest -q --cov=app --cov-report=term-missing
```

That command passed here: 6 tests, no coverage floor. There is no `pytest.ini`, `pyproject.toml`, or `.coveragerc`.

`ruff check app tests` is what CI runs. On this tree it reports `F401` for the unused import `SUPPORTED_LOCALES` in `backend/app/routers/translate.py`. There is no `ruff` config file. `black` and `isort` are not dependencies.

`.github/workflows/ci.yml` runs on pushes to `main` and on pull requests into `main`:

- Backend job, directory `backend/`, Python 3.12: `pip install -r requirements.txt`, then `pip install pytest pytest-cov ruff`, then `ruff check app tests`, `python -c "import app.main"`, and `pytest -q --cov=app --cov-report=term-missing` with `LOCALIZATION_PROVIDER=mock`.
- Frontend job, Node 20: `npm ci` using `frontend/package-lock.json`, then `npm run lint`, `npx tsc --noEmit`, and `npm run test -- --run`.

`frontend/package-lock.json` is not in the tree, so `npm ci` has nothing to install from. There is no ESLint config file. `npm run lint` exits because ESLint finds no config. There is no Vitest config and no `*.test` or `*.spec` file. `npm run test -- --run` exits because Vitest finds no tests. `frontend/tsconfig.json` has `"strict": true`. `npx tsc --noEmit` completed with exit code 0 in a local check. `npm run build` completed and wrote `frontend/dist`, which `.gitignore` ignores.

`scripts/smoke.py` is not a CI step.

## Environment

Names below are the ones `backend/app/config.py` loads. Comments in `.env.example` match this list. Placeholder keys in that file are not real credentials. `.gitignore` ignores `.env`.

| Variable | Role in code |
| --- | --- |
| `LOCALIZATION_PROVIDER` | `openai`, `anthropic`, `ollama`, or `mock`. Default `mock`. |
| `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_BASE_URL` | OpenAI client. Defaults `gpt-4o-mini` and `https://api.openai.com/v1`. |
| `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` | Anthropic client. Default model `claude-3-5-haiku-latest`. |
| `OLLAMA_BASE_URL`, `OLLAMA_MODEL` | Ollama client. Defaults `http://localhost:11434` and `llama3.1:8b`. |
| `HOST`, `PORT` | Stored on `Settings` (`0.0.0.0`, `8000`). No module reads them to bind a socket. The listen address is uvicorn's `--host` and `--port`. |
| `LOG_LEVEL` | Compared with `debug` in the exception handler. It does not configure a logger. Default `info`. |
| `CORS_ORIGINS` | List of origins. In `.env`, pydantic-settings parses this as JSON. A bare URL raises `SettingsError` while loading `.env`. The example uses `["http://localhost:5173"]`. |
| `RATE_LIMIT_PER_MINUTE` | Passed to the slowapi default limit. Default `60`. |

`SMOKE_BASE_URL` is read only by `scripts/smoke.py`.

## Not in this tree

- `backend/app/redaction.py`, or any other redaction module
- an OpenAPI-generated TypeScript client
- `CONTRIBUTING.md` and `SECURITY.md`
- a glossary cache, per-tenant glossary, or cost telemetry
- `package-lock.json`, an ESLint config, a Prettier config, or a frontend test

## License

MIT. `LICENSE` is copyright 2026 Zekk-s. `.github/CODEOWNERS` lists `@Zekiog` for the tree.
