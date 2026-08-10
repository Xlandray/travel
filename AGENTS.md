# AGENTS.md

Armonitex Travel monorepo: three packages + ops tooling, all orchestrated via Docker.

## Layout

- `backend/` — FastAPI + async SQLAlchemy + Alembic (Python 3.12). Entry: `app/main.py`, routes under `app/api/v1/routes/`.
- `admin-panel/` — Refine (React 18 + Vite + TypeScript) CMS. Entry: `src/main.tsx`, pages under `src/pages/`.
- `frontend/` — Next.js 16 customer site. App Router under `src/app/`.
- `docs/adr/` — Architecture Decision Records, written in Turkish, append-only (new decisions get the next number).
- `scripts/` — `master_orchestrator.py` QA gate + ssh runner scripts.

**Directory gotcha:** `docker-compose.prod.yml`, `docs/ARCHITECTURE_AND_HANDOVER.md`, and `scripts/master_orchestrator.py` still reference `armonitex-web/`, but the web app now lives in `frontend/`. Do not create `armonitex-web/`.

## Local development

1. `cp .env.example .env` at root and replace every placeholder with a unique secret (`JWT_SECRET_KEY` must be ≥32 chars — enforced by `backend/app/core/config.py`).
2. `docker compose up --build` runs `db` → one-off `migrate` (alembic) → `api` (uvicorn --reload) → `admin-panel` → `armonitex-web`.
3. Ports: API default host port `8081` (`API_PORT`), admin `5181`, web `3010`. OpenAPI at `http://localhost:8081/docs`.
4. DB has **no host port mapping**; inspect via `docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"`. `docker-compose.prod.yml` maps it — prod only.
5. First admin (idempotent, run once): `docker compose run --rm --no-deps -e ADMIN_EMAIL -e ADMIN_PASSWORD api python -m app.scripts.bootstrap_superuser`.

Only file mounts are `backend/app`, `admin-panel/src`, `frontend/src`, `frontend/public`; restart the relevant container after changes to `pyproject.toml`, `package.json`, docker files, or alembic config.

## Backend

- No backend test framework or tools are configured (no pytest deps in `pyproject.toml`). Verification = `ruff check . && ruff format --check .` (line-length 100, py312) run from `backend/`.
- `DATABASE_URL` **must** use the `postgresql+asyncpg://` scheme; the validator in `config.py` and `alembic/env.py` both reject anything else. Alembic migrations require `DATABASE_URL` in the environment.
- New models: add them so `app/models/__init__.py` imports them — `alembic/env.py` works off `Base.metadata` via `import app.models`. Generate new migrations with the `migrate` flow, never edit applied ones.
- Layered structure: `routes/` → `services/` → `repositories/` → models, with Pydantic schemas and `schemas/__init__.py` re-exports. Match existing patterns when adding features (see tours/bookings/upload for the newest examples).
- Uploaded tour media is saved to `backend/media/tours` (volume `tour_media_data`) and served at `/media`. Tour images must be jpeg/png/webp/gif, ≤10MB (`routes/upload.py`).
- A booking sweeper background task runs in the app lifespan (`core/tasks.py`); restart the api container if lifecycle behavior changes.
- CORS is restricted to `CORS_ALLOWED_ORIGINS` (env, JSON list); dev default includes `:5173` and `:3000`.

## Frontend (customer site)

- **Next.js 16 has breaking API changes.** Read the relevant guide in `node_modules/next/dist/docs/` before writing code — see `frontend/AGENTS.md`, which is auto-reappended by `next dev`; keep it committed, don't fight it.
- **Design system rule (ADR-0007):** ad-hoc color classes (`bg-slate-*`, `gray-*`, `black`, `zinc-*`) are banned in components. Use the semantic token classes (`.bg-surface-token`, `.text-brand-token`, `.card-token`, `.btn-primary-token`, etc.) defined in `src/app/globals.css`; change colors only via the `--color-*` variables there.
- i18n via `src/locales/{tr,en}.json` + `src/lib/i18n.ts` (dictionary-based switcher).
- Commands (from `frontend/`): `npm run lint` (eslint), `npm run build`. E2E: `npm run test:e2e` (Playwright, chromium only) — requires a built+served app on `:3000`; the config webserver runs `npm run start` and writes JSON to `frontend/agent-report/test-results.json`, which `scripts/master_orchestrator.py` consumes.

## Admin panel

- `npm run lint` (eslint), `npm run build` (`tsc -b && vite build`).
- `VITE_API_URL` (dev: `http://localhost:8081/api/v1`) is baked in at build time via the Docker env; the `dataProvider` in `src/providers/` targets FastAPI resource paths (`/api/v1/**`).
- List endpoints must conform to the Refine dataProvider contract: `GET {resource}?page=&page_size=` returning `{data: [...], total}`; `create` uses POST, `update` uses PATCH. New backend list routes must match this shape (`schemas/pagination.py`).

## Commits

- Do not commit placeholders or real secrets; `.env` files are gitignored. `armonitex_api.egg-info/` and `agent-report/` outputs are build artifacts — leave them out of commits.