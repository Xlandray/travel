# AGENTS.md

Armonitex Travel monorepo: three packages + ops tooling, all orchestrated via Docker.

## Layout

- `backend/` — FastAPI + async SQLAlchemy + Alembic (Python 3.12). Entry: `app/main.py`, routes under `app/api/v1/routes/`.
- `admin-panel/` — Refine (React 18 + Vite + TypeScript) CMS. Entry: `src/main.tsx`, pages under `src/pages/`.
- `frontend/` — Next.js 16 customer site. App Router under `src/app/`.
- `docs/adr/` — Architecture Decision Records, written in Turkish, append-only (new decisions get the next number).
- `scripts/` — `master_orchestrator.py` QA gate + ssh runner scripts.

**Directory gotcha:** `docs/ARCHITECTURE_AND_HANDOVER.md` and `scripts/master_orchestrator.py` still reference `armonitex-web/`, but the web app now lives in `frontend/`. Do not create `armonitex-web/`. (`docker-compose.prod.yml` used to as well, which is why the production stack could not build; it no longer does.)

## Production

Self-hosted on an always-on machine, published through a Cloudflare Tunnel. The customer site is on Vercel; only the API and the admin panel run on the box.

```
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

- **No host ports are published.** `cloudflared` dials out and reaches the other services over the compose network, so the machine needs no inbound firewall rule. Map the hostnames in the Cloudflare dashboard: `api.<domain>` → `http://api:8000`, `admin.<domain>` → `http://admin-panel:80`.
- **`--forwarded-allow-ips *` on the api command is load-bearing.** Upload responses are built from `request.base_url`, and those URLs are stored in the database. Without the flag the app ignores `X-Forwarded-Proto` and returns `http://…` behind the tunnel — verified: with the flag a request carrying `X-Forwarded-Proto: https` yields `https://api.example.com/media/…`, without it the same request yields `http://`. The browser blocks that as mixed content on the HTTPS panel, and the wrong URL is persisted. Trusting all peers is safe here only because no port is published.
- The api runs 4 gunicorn workers, so 4 copies of the booking sweeper. That is safe: it claims rows with `FOR UPDATE SKIP LOCKED`, so workers divide the work instead of releasing seats twice.
- Uploaded media lives in the `tour_media_prod_data` volume. It is a named volume, not a bind mount — do not `docker compose down -v` in production.
- `admin-panel` builds its `prod` stage: a real `vite build` served by nginx with SPA fallback. The dev stage (Vite dev server) is what `docker-compose.yml` uses. `VITE_API_URL` is inlined at build time, so changing it needs a rebuild, not a restart.
- Copy `.env.prod.example` to `.env.prod` on the host. `CORS_ALLOWED_ORIGINS` must list the Vercel origin **and** the admin origin, exactly.
- **Vercel needs `NEXT_PUBLIC_API_URL` set to the public API URL and a redeploy.** It is inlined at build time. Without it the deployed bundle falls back to `http://localhost:8081/api/v1`, which in a visitor's browser means their own machine — the site loads but every API call fails silently.

## Local development

1. `cp .env.example .env` at root and replace every placeholder with a unique secret (`JWT_SECRET_KEY` must be ≥32 chars — enforced by `backend/app/core/config.py`).
2. `docker compose up --build` runs `db` → one-off `migrate` (alembic) → `api` (uvicorn --reload) → `admin-panel` → `armonitex-web`.
3. Ports: API default host port `8081` (`API_PORT`), admin `5181`, web `3010`. OpenAPI at `http://localhost:8081/docs`.
4. DB has **no host port mapping**; inspect via `docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"`. `docker-compose.prod.yml` maps it — prod only.
5. First admin (idempotent, run once): `docker compose run --rm --no-deps -e ADMIN_EMAIL -e ADMIN_PASSWORD api python -m app.scripts.bootstrap_superuser`.

Only file mounts are `backend/app`, `admin-panel/src`, `frontend/src`, `frontend/public`. Restart/rebuild policy per container:

- `api` runs uvicorn `--reload` → mount `backend/app` is live; restart only after changes to `pyproject.toml`, alembic config, or lifespan behavior.
- **A new migration needs a rebuild.** `backend/alembic` is not mounted, so a freshly written revision exists only on the host: `docker compose run --rm api alembic upgrade head` reads the copy baked into the image, reports it is already at head and does nothing, while the mounted `app/` already expects the new column. The result is a 500 on every query touching that table. Run `docker compose up -d --build migrate api` after adding a revision. (The backend suite is unaffected — it migrates its own database through the `test` image, which is rebuilt each run.)
- `admin-panel` runs Vite dev server → mount `admin-panel/src` is live.
- `armonitex-web` runs **`next start` (production build)** — the Dockerfile compiles `frontend/src` at image build time, so mount `frontend/src`/`frontend/public` does **NOT** take effect on their own. **Always run `docker compose up -d --build armonitex-web`** after any frontend code change; a plain `docker compose restart` keeps serving the stale build. (This is why the live checkout looked "dark/grey" after the token refactor — the old build was still being served.)
- Any change to `package.json`, docker files, or alembic config requires a full rebuild of the affected service.

## Backend

- Verification, all four gates in the image CI uses (from the repo root):
  `docker compose run --rm --entrypoint sh test -c "ruff check . && ruff format --check . && mypy && pytest"`.
  Run them there, not off your host PATH — the `test` image installs `.[test,dev]`, so ruff and mypy are the pinned versions. A stray older ruff on PATH will disagree with the pre-commit hook about formatting.
- Tests live in `backend/tests/` and run against a real PostgreSQL. `conftest.py` drops, recreates and migrates a separate `${POSTGRES_DB}_test` database through the real Alembic chain on every run, so the dev database is never touched and a migration that will not apply fails the suite. Each test's session is rolled back afterwards, so tests do not see each other's rows. pytest/httpx live in the `test` extra and are installed only into the image built by the `test` compose service (`INSTALL_TEST=true`), keeping them out of the runtime image.
- The test session sets `expire_on_commit=False` to match `AsyncSessionLocal`. With the default, every commit expires the loaded objects and the next attribute read emits IO, which raises `MissingGreenlet` under an async session — a failure production never produces. The fixture has to run app code under production's session semantics or the suite invents bugs and hides real ones.
- `conftest.py` overrides **only** `get_session`. Authentication is not mocked at all: `api(user)` builds a client per account carrying a real bearer token, so the whole dependency chain runs. Do not reintroduce a `get_current_user` override — the earlier version handed every fixture the same client object, so in a test using both `admin_client` and `customer_client` whichever fixture was built last silently decided who all the requests came from, and an admin request would fail as the customer for the wrong reason.
- Booking and payment tests assert the seat ledger (`assert_seats_balance` fixture): `available_seats + seats held by non-cancelled bookings == total_quota`. Assert it after any transition that touches seats — a route can return the right status code while overselling the bus.
- **Locking rules for the seat and money paths.** Use `booking_service.lock_booking` / `lock_departure` / `payment_service._lock_payment` rather than a bare `with_for_update()`. They add `populate_existing=True`, which is load-bearing: if the row is already in the session's identity map (and it is, because routes load it to check ownership), SQLAlchemy returns the cached object and discards what the locking SELECT read — the lock is held but the status check runs on stale data. Read every status *after* taking the lock, never before. Acquire in the order **booking → payment → departure**; a path that reverses it can deadlock against the others. `tests/test_concurrency.py` covers all of this and is verified to fail when the order is reversed.
- Concurrency tests cannot use the shared rolled-back `session` fixture — `SELECT ... FOR UPDATE` never blocks against your own transaction, so a missing lock looks identical to a working one. `test_concurrency.py` runs each request on its own session from a real sessionmaker, mints real tokens with `create_access_token` (so requests can come from different accounts, and the token path gets exercised), commits for real and deletes its rows in the fixture teardown.
- Expired-cart cleanup has exactly one implementation: the lifespan sweeper (`core/tasks.start_booking_sweeper` → `cleanup_service.release_expired_bookings`). Do not re-add a per-request `BackgroundTasks` timer — it dies on restart, holds an asyncio task per booking for 15 minutes, and blocks any client that waits for background tasks to finish (which made the booking tests hang).
- `pythonpath = ["."]` in `[tool.pytest.ini_options]` is load-bearing: without it `import app` resolves to the copy `pip install .` baked into site-packages at build time instead of the mounted working tree, and the suite silently passes against stale code.
- `DATABASE_URL` **must** use the `postgresql+asyncpg://` scheme; the validator in `config.py` and `alembic/env.py` both reject anything else. Alembic migrations require `DATABASE_URL` in the environment.
- New models: add them so `app/models/__init__.py` imports them — `alembic/env.py` works off `Base.metadata` via `import app.models`. Generate new migrations with the `migrate` flow, never edit applied ones.
- Layered structure: `routes/` → `services/` → `repositories/` → models, with Pydantic schemas and `schemas/__init__.py` re-exports. Match existing patterns when adding features (see tours/bookings/upload for the newest examples).
- A departure's `total_quota` and `available_seats` are two halves of one ledger: the difference between them is what passengers are holding. Never write either blindly. `PATCH /tour-departures/{id}` resizes the bus by shifting `available_seats` by the same delta, refuses (409) a quota below the seats already sold, and refuses (422) `available_seats > total_quota` — the seat invariant is reachable from this endpoint just as much as from booking.
- List endpoints shared by the public site and the admin panel (`/tours`, `/tour-categories`) return only active rows by default and accept `include_inactive=true`, which requires a superuser (`OptionalUser` in `api/deps.py` — signed in widens what you may ask for, it does not gate entry). Without it, deactivating a row hides it from the only screen that could bring it back. The admin `dataProvider` sends the flag on every list; endpoints that do not support it ignore it.
- There is no placeholder catalogue. `GET /tours` returns `[]` when nothing is published and `GET /tours/{slug}` 404s for anything not in the database. Both the backend `DEFAULT_TOURS` fallback and the frontend's `SAMPLE_TOURS` initial state were removed: they advertised two invented trips (`kapadokya-turu`, `salda-golu-ve-pamukkale`) with departure ids that did not exist, so a fresh database sold trips nobody could book. Do not reintroduce fixture data on a read path — seed the database instead.
- Uploaded tour media is saved to `backend/media/tours` (volume `tour_media_data`) and served at `/media`. The accepted format is decided by magic bytes, not by the client's `Content-Type`, and the allow-list in `image_pipeline.PIL_SUPPORTED` is load-bearing: without it anything Pillow can decode (BMP, TIFF, ICO…) would be accepted. The 10MB cap is enforced while reading, one chunk at a time — do not go back to `await file.read()` then checking the length, which makes the server buffer the whole file before refusing it.
- Setting keys are dot-namespaced (`site.iletisim.adres`), matching what the customer site looks up. The pattern lives in `schemas/setting.SETTING_KEY_PATTERN` and is duplicated in the admin `SettingsForm` — the two must move together.
- `GET /public/settings` returns **every** setting's value to anonymous callers; `Setting` has no public/private flag. Today all of them are genuinely public (contact details, social links, deposit rate), but there is nowhere to keep a private one. Do not store a credential in a Setting until that is fixed.
- `PATCH /admin/users/{id}` refuses to demote or deactivate the last active superuser (409). Removing it leaves an installation with no account that can administer it and no endpoint that can grant the privilege back.
- `POST /contact` is anonymous and sends an email per request, with no rate limit — an open trigger for outbound mail. Worth putting behind a limiter before launch. Its `full_name` goes into the Subject header, so the schema refuses control characters: Python's email layer rejects CR/LF in a header by raising, and an uncaught raise on a public form is a 500.
- A booking sweeper background task runs in the app lifespan (`core/tasks.py`); restart the api container if lifecycle behavior changes.
- CORS is restricted to `CORS_ALLOWED_ORIGINS` (env, JSON list); dev default includes `:5173` and `:3000`.
- JWTs carry a `type` claim and `core/security._decode` refuses any token of the wrong type. Session tokens (`access`) and password reset tokens (`password_reset`) are not interchangeable: a stolen session token must not be able to change a password, and a reset link must not work as an API key. Reset tokens also embed `password_reset_fingerprint(hashed_password)`, which is re-checked on use — changing the password invalidates the link, which is what makes it single-use without a table of issued tokens. Any new token kind gets its own type constant. Every token also carries a random `jti`; without it two logins by the same account in the same second produce byte-identical strings, and one session cannot be spoken about separately from another.
- **Session revocation.** Access tokens are self-contained, so the server has nothing to delete when one leaks. `users.token_version` is the recall mechanism: `create_access_token(subject, token_version)` stamps the token, `UserService.get_authenticated_user` compares it on every request, and bumping the column kills every token issued so far at once. Consequences to keep in mind:
  - `create_access_token` takes the version as a **required** argument. Do not give it a default — a call site that forgets it would silently mint an unrevokable token.
  - A token with no `tv` claim is refused, so deploying the column signs everyone out once. That is deliberate: treating a missing claim as "any version" would exempt exactly the tokens that cannot be recalled.
  - Bumps are written as `user.token_version = User.token_version + 1` (a SQL expression), never read-modify-write. Two overlapping revocations would otherwise both compute the same new number, and a token minted between them would survive being revoked twice. `test_concurrency.py` pins this down by loading the row in two sessions before either commits.
  - Revocation happens on: `POST /auth/logout-all` (the account's own), `POST /auth/reset-password` (a reset is often a response to a takeover, so the attacker's session has to die with the old password), `POST /admin/users/{id}/revoke-sessions`, and `PATCH /admin/users/{id}` when `is_active` goes false — without that last one, re-enabling a suspended account would bring back whichever token caused the suspension.
  - Revoking is not suspending: the account stays usable and the person logs in again. That is the whole point of having it alongside `is_active`.

## Frontend (customer site)

- **Next.js 16 has breaking API changes.** Read the relevant guide in `node_modules/next/dist/docs/` before writing code — see `frontend/AGENTS.md`, which is auto-reappended by `next dev`; keep it committed, don't fight it.
- **Live container gotcha:** the `armonitex-web` container serves a **production build** (`next start`), so after ANY change under `frontend/src` or `frontend/public` you must run `docker compose up -d --build armonitex-web` — restart alone serves the stale build and the change will appear "not working".
- **Design system rule (ADR-0007):** ad-hoc color classes (`bg-slate-*`, `gray-*`, `black`, `zinc-*`) are banned in components. Use the semantic token classes (`.bg-surface-token`, `.text-brand-token`, `.card-token`, `.btn-primary-token`, etc.) defined in `src/app/globals.css`; change colors only via the `--color-*` variables there.
- i18n via `src/locales/{tr,en}.json` + `src/lib/i18n.ts` (dictionary-based switcher).
- Commands (from `frontend/`): `npm run lint` (eslint), `npm run build`.
- **E2E** (`npm run test:e2e`, Playwright, chromium only) runs against the compose stack, not a server it starts itself: `docker compose up -d --build` first, then the suite hits the web app on `:3010`, the API on `:8081` and the admin panel on `:5181`. Override with `PLAYWRIGHT_TEST_BASE_URL` / `NEXT_PUBLIC_API_URL` / `ADMIN_PANEL_URL`. It still writes `frontend/agent-report/test-results.json` for `scripts/master_orchestrator.py`.
  - `tests/e2e/preflight.ts` is a `globalSetup` that refuses to run unless both services answer **and** the page really is this site. The config used to start `next start` on `:3000` with `reuseExistingServer`, so on a machine with another project up the suite silently tested that project. Do not put `webServer` back.
  - The specs seed their own tour and departure through the API (`tests/e2e/seed.ts`) instead of picking whatever is in the database, so they work on a clean one. That needs the superuser to exist: `docker compose run --rm --no-deps -e ADMIN_EMAIL -e ADMIN_PASSWORD api python -m app.scripts.bootstrap_superuser`. Credentials come from `E2E_ADMIN_EMAIL` / `E2E_ADMIN_PASSWORD`.
  - CI runs it in the `e2e` job, which is also the only proof that `docker compose up --build` works from a clean checkout.
  - Two projects, `desktop` and `mobile` (Pixel 5), and the whole suite runs on both — Stage 5's exit criterion asks for the critical journeys on both. Anything that only exists on one layout has to handle the other: `showcase.spec.ts` opens the header menu when the toggle is visible, because on a phone the nav lives behind it.
  - `purchase-journey.spec.ts` is the one that matters: register → log in → book → pay → see it confirmed, all through the UI, ending with an API read that checks the seats actually moved. A UI that reports success without booking anything cannot pass it. The card fields on `/odeme` are `required` in the markup but never sent anywhere, so the test fills them.
  - `accessibility.spec.ts` scans the purchase path with axe. **`critical` fails the build; `serious` is only annotated.** Today every `serious` finding is colour contrast, and it is not a component bug: the brand colour `--color-primary: #14b8a6` is 2.49:1 against white, under even the 3.0:1 large-text threshold, so all 55 nodes on the landing page are the same root cause. `#0f766e` (teal-700) would give 5.47:1 and clear AA. That is a visual identity decision — make it, then promote `serious` to blocking in that spec.
  - `session-revocation.spec.ts` holds a second, API-minted session for the same account as the browser, then clicks "Tüm Cihazlarda Oturumu Kapat" and asserts that other session is dead. Asserting only on the clicking browser would pass against an ordinary local logout, which is exactly the thing this feature exists to be better than.
  - Labels must be associated with their control (`htmlFor` + `id`). Several selects and inputs looked labelled but were not, which makes them unidentifiable to a screen reader; axe catches this as `label` / `select-name`.

## Admin panel

- `npm run lint` (eslint), `npm run build` (`tsc -b && vite build`).
- `VITE_API_URL` (dev: `http://localhost:8081/api/v1`) is baked in at build time via the Docker env; the `dataProvider` in `src/providers/` targets FastAPI resource paths (`/api/v1/**`).
- List endpoints must conform to the Refine dataProvider contract: `GET {resource}?page=&page_size=` returning `{data: [...], total}`; `create` uses POST, `update` uses PATCH. New backend list routes must match this shape (`schemas/pagination.py`).

## Quality gates

- `pre-commit install` once per clone. Hooks: whitespace/EOF/line-ending fixers, YAML/JSON/TOML validity, private-key and **gitleaks** secret scanning, `ruff check --fix` + `ruff format` over `backend/`, and prettier over `frontend/src` and `admin-panel/src`. Run everything with `pre-commit run --all-files`.
- `.github/workflows/ci.yml` runs the same hooks plus pytest, both npm lint/build pairs, and an api image build — so a commit pushed with `--no-verify` is still caught. It is verified to reject a bad change, not just to pass.
- Local tooling comes from the extras: `pip install ".[test,dev]"` from `backend/` gets pytest and the pinned ruff. CI installs the same thing.
- The ruff version is pinned in **two** places that must move together: the `dev` extra in `backend/pyproject.toml` and `rev:` in `.pre-commit-config.yaml`. Different ruff versions can disagree about formatting and the two gates will fight.
- Type checking is **mypy**, configured in `[tool.mypy]` and pinned in the `dev` extra. Run `mypy` from `backend/`; CI runs it in the backend job. It is not a pre-commit hook: pre-commit would run it in an isolated environment without the project's dependencies and report imports it cannot resolve.
- mypy runs with `strict = true`, and the tree passes it with **no** `# type: ignore` comments and no per-module opt-outs. The only relaxation is `ignore_missing_imports` for `asyncpg.*`, which ships no `py.typed`. Keep new code strict rather than adding ignores.
- prettier is a devDependency of each npm project (single pinned version) and configured repo-wide by `.prettierrc.json` (printWidth 100, matching ruff's line-length). There is no black: `ruff format` is black-compatible and replaced it.

## Commits

- Do not commit placeholders or real secrets; `.env` files are gitignored. `armonitex_api.egg-info/` and `agent-report/` outputs are build artifacts — leave them out of commits.
