# AGENTS.md

Notes for people and agents editing this repository. Describe the behavior that is in the files. Do not add docs for routes, providers, clients, or modules that are not in the tree.

## What is here

- `backend/app` is a FastAPI app. Routes are in `main.py`, `routers/health.py`, and `routers/translate.py`.
- `LOCALIZATION_PROVIDER` is defined in `backend/app/config.py` and read by `get_engine()` in `backend/app/translate/engine.py`.
- Locale codes the API accepts are the keys of `SUPPORTED_LOCALES` in `backend/app/locales.py`.
- `frontend/src/App.tsx` loads `GET /v1/locales` and posts `POST /v1/translate` on submit.
- `scripts/smoke.py` calls a running server. It is not part of CI.
- `README.md` lists the routes, env vars, and dependencies.

## Secrets

Do not commit `.env`, API keys, or real credentials. `.gitignore` ignores `.env`. Placeholders belong in `.env.example`. Provider keys are read by the backend provider modules. Do not put them in `frontend/`.

## Commands

From `backend/` (this is also the CI working directory, and the directory where `import app` works):

```bash
pip install -r requirements.txt
pytest -q --cov=app --cov-report=term-missing
ruff check app tests
uvicorn app.main:app --reload --port 8000
```

CI sets `LOCALIZATION_PROVIDER=mock` for pytest. The checked-in tests use the mock provider. `ruff check app tests` currently reports an unused import of `SUPPORTED_LOCALES` in `backend/app/routers/translate.py`. There is no coverage floor in the repo.

From `frontend/`:

```bash
npm install
npm run dev
```

`package.json` also defines `build`, `preview`, `lint`, and `test`. The tree has no `package-lock.json`, no ESLint config, and no frontend test file. `.github/workflows/ci.yml` still runs `npm ci`, `npm run lint`, `npx tsc --noEmit`, and `npm run test -- --run` on Node 20. The backend CI job uses Python 3.12.

## Tools that are present

- `ruff` is in `backend/requirements.txt`. CI runs `ruff check`. There is no `ruff` config file.
- `frontend/tsconfig.json` sets `"strict": true`.
- ESLint and the TypeScript ESLint packages are devDependencies. Prettier, `black`, and `isort` are not dependencies.

## Pull requests

`.github/PULL_REQUEST_TEMPLATE.md` is the template. `.github/workflows/ci.yml` runs on pull requests into `main`.

When a change adds an environment variable, update `.env.example` and `backend/app/config.py` together. When a change adds a locale code the API should accept, update `backend/app/locales.py` and the tests that assert the locale list.
