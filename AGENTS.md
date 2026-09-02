# AGENTS.md — Working Agreement for AI Agents and Human Contributors

This file governs how AI agents (Copilot, Claude, Cursor, etc.) and humans contribute to
`ai-localization-demo`. **Read before opening a PR.**

## Scope

- This repo ships a production-shaped FastAPI reference for AI-driven localization.
- Out of scope: business landing pages, marketing copy, deep model fine-tuning.

## Hard rules

1. **Never commit `.env`, API keys, or real credentials.** Use `.env.example` only.
2. **Never add a new provider without updating `LOCALIZATION_PROVIDER` docs and tests.**
3. **Never hard-code locale strings outside `app/locales.py`.**
4. **Public surface lives under `/v1/*`.** Internal helpers stay under `/internal/*`.
5. **No telemetry or analytics keys** in the demo frontend.

## Workflow

```text
issue → branch → PR → CI green → human review → squash merge to main
```

- Branch names: `feat/<scope>`, `fix/<scope>`, `chore/<scope>`, `docs/<scope>`.
- Commit subjects ≤ 72 chars, body wraps at 100.
- One logical change per PR. Reformatting goes in a separate `chore:` PR.
- Agents propose via PR. **Humans approve before merge to `main`.**

## Testing

- Backend: `pytest backend/tests` — must pass 100 %.
- Frontend: `npm run test` — must pass 100 %.
- Smoke test: `python scripts/smoke.py` against a running uvicorn.
- Coverage floor: 80 % for `app/translate/`, 60 % repo-wide.

## Code style

- Python: `ruff` + `black` (line-length 100). Type hints mandatory on public functions.
- TypeScript: `eslint` (Airbnb) + `prettier`. `strict: true` in `tsconfig.json`.
- Imports sorted by `isort` / `eslint-plugin-import`.

## Review expectations

For a PR to be merged, the description must answer:

- What does this change do, and why now?
- Which tests cover it?
- What could break?
- Does it touch the public API or `/v1/*` contracts?
- Are there new environment variables? (Update `.env.example`.)

## Observability

- Every public endpoint emits a structured log line with `request_id`, `latency_ms`,
  `provider`, `tokens_in`, `tokens_out`.
- Errors include a stack trace only when `LOG_LEVEL=debug`.

## Out of band

- Coordination with sibling repos under `@Zekk-s` happens via PR cross-links,
  not direct pushes.
- Production secrets are managed by the deployment platform, never this repo.