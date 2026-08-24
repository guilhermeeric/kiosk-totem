# AGENTS.md

Instructions for AI coding agents working in this repo. Humans: the READMEs
(`README.md`, `backend/README.md`, `frontend/README.md`) cover setup and
endpoints; this file covers conventions and ground truth agents need.

## Project

Self-service checkout ("totem") for a fast-food kiosk: browse menu → build
cart → simulated payment → order → kitchen/visor status flow → tracking, with
QR handoff between the kiosk and a phone. Backend: FastAPI + asyncpg +
PostgreSQL, clean architecture under `backend/src/`. Frontend: Vue 3 + Vite +
TypeScript under `frontend/` (Tailwind v4 + shadcn-vue, TanStack Query, vitest).

## Design philosophy

Build the simplest complete system. Trace behavior and invariants before
editing. Prefer in order: reuse what exists; extend the layer that owns the
concern; use stdlib/framework/database features; add a small new
implementation where the invariant belongs; refactor when structure obstructs
ownership. Optimize total system complexity — not diff size. Fix root cause.
Avoid speculative features and single-implementation interfaces; an interface
is justified by a real seam or lifecycle cost — say which. Simplicity never
drops trust-boundary validation, security, error handling, migration safety,
concurrency protection, or required tests. Run the smallest sufficient proof;
stop when the task is satisfied.

## Layout

Backend (`backend/src/`), imports point inward `http -> usecases -> domain <- infrastructure`:
- `http/` — FastAPI app + Pydantic schemas (DTOs); the only layer importing FastAPI.
- `usecases/` — application logic; one class per use case exposing only `.execute()`; async; depends on domain only.
- `domain/` — entities (dataclasses), StrEnum state enums, repository ABCs. Pure Python, no I/O.
- `infrastructure/database/` — asyncpg adapters implementing the ABCs, one `asyncpg.Connection` per repo; liquibase migrations live here.
- `tests/` — colocated: `tests/domain`, `tests/usecase`, `tests/infrastructure`.

The repository ABCs in `domain/repositories.py` are a deliberate seam: usecases
depend on them, tests mock them with `AsyncMock(spec=...)`, Postgres adapters
implement them. Keep the seam; don't add interfaces speculatively.

Frontend (`frontend/src/`):
- `views/` (routes), `components/` (UI primitives in `components/ui/`), `composables/` (server-state hooks), `domain/` (pure logic), `api/client.ts` (typed client), `router/`.
- `domain/api.ts` is GENERATED from `openapi.json` via `npm run generate:api` — never hand-edit; regenerate after backend API changes.
- Specs live next to their code in `__tests__/`.

## Commands

From repo root, `make` lists targets. Key ones:
- `make check` — backend gate: ruff lint + format check + pytest
- `make test`, `make openapi` (regenerate `openapi.json`), `make reset` (wipe dev DB volume)
- Backend (from `backend/`): `uv sync`, `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`, `uv run python -m src.main` — env vars `APP_HOST`, `APP_PORT`, `APP_RELOAD`, `DATABASE_URL`; the default connects to localhost Postgres (dev creds `totem`/`totem`)
- Frontend (from `frontend/`): `npm test` (vitest), `npm run build` (vue-tsc + vite — the type gate), `npm run dev`
- Full stack: `docker compose up -d --build` from `backend/` (postgres + liquibase migrations + backend + frontend); `docker compose run --rm liquibase` re-runs migrations

Schema changes go through liquibase changesets in
`backend/src/infrastructure/database/migrations/` (formatted SQL, unique
`totem:N` ids, rollbacks per changeset). There is no deployed DB, so editing an
existing changeset is allowed — then `make reset` and bring the stack back up.

Quality gate before committing: `make check` AND `npm test && npm run build`
(from `frontend/`) must pass.

## Code style

Backend:
- Guard clauses and early returns; validate at the top and raise `ValueError` before doing work.
- Money is `Decimal` in the domain; convert to `str` only at the HTTP boundary.
- State enums are `StrEnum`, persisted as `.value`.
- Value objects are frozen dataclasses; aggregates with transitions are mutable dataclasses with explicit methods that raise `ValueError` on illegal transitions (`Order.mark_*`).
- Repos: `get_*` returns `None` when not found; `create`/`update` raise `ValueError` on wrong id state or 0 rows; translate `UniqueViolationError` → `ValueError`.
- Async only where I/O happens; domain logic is synchronous. New async tests need no `@pytest.mark.asyncio` (`asyncio_mode = "auto"`).
- FastAPI wiring uses the `lifespan` context manager — never `@app.on_event`.
- `http/exceptions.py` owns error translation: domain `NotFound` subclasses → 404, other `ValueError` → 400.

Frontend:
- Server state via TanStack Query; the API response is authoritative on every call.
- Money arrives as `str` from the backend; format with `domain/money.ts` (pt-BR, BRL).
- Session identity is the `composables/useSession.ts` singleton (sessionStorage); `session_id` is the bearer capability — there is no auth.

## Testing

- Backend: usecase tests mock repo ABCs with `AsyncMock(spec=...)`; domain tests use plain instances. Coverage is on by default; `http/`, `schemas/`, `infrastructure/` are omitted (covered via the live stack). Infra repo tests hit real Postgres through `TEST_DATABASE_URL` and skip when the DB is down.
- Frontend: vitest + happy-dom, specs colocated in `__tests__/`.
- New behavior ships with tests.

## Git workflow

- Conventional Commits (`feat:`, `fix:`, `refactor:`, `chore:`).
- Small commits directly on `main`; keep it green (quality gate above).
- All GitHub interaction goes through the `gh` CLI.
