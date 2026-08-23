# AGENTS.md

Instructions for AI coding agents working in this repo. Humans: the READMEs
(`README.md`, `backend/README.md`) cover setup and endpoints; this file covers
conventions and ground truth that agents need.

## Project

Self-service checkout ("totem") backend for a fast-food kiosk: FastAPI + asyncpg +
PostgreSQL, clean architecture under `backend/src/`. A Vue frontend is planned but
nothing exists yet — all code lives in `backend/`.

## Design philosophy

Build the simplest complete system. Trace behavior and invariants before editing.
When implementing, prefer in order: reuse what already exists; extend the layer,
type, or helper that owns the concern; use stdlib/framework/database features;
add a small new implementation where the invariant belongs; refactor when the
structure obstructs clear ownership. Optimize total system complexity, clarity,
and ownership — not diff size. Fix root cause. Avoid speculative features,
premature abstractions, and single-implementation interfaces — an interface is
justified by a real seam or lifecycle cost; say which. Simplicity never drops
trust-boundary validation, security, error handling, migration safety, concurrency
protection, or required tests. Run the smallest sufficient proof; stop when the
task is satisfied.

## Layout and dependency rule

- `src/http` — FastAPI app and Pydantic request/response schemas (DTOs). The only
  layer that imports FastAPI.
- `src/usecases` — application logic (e.g. `ListItems`). Async; depends on domain only.
- `src/domain` — entities (dataclasses), StrEnum state enums, repository ABCs.
  Pure Python, no I/O, never imports other layers.
- `src/infrastructure/database` — asyncpg adapters implementing the repository ABCs.
  Each repo is constructed with a single `asyncpg.Connection`.
- `src/tests` — tests colocated with the code they cover: `src/tests/domain`,
  `src/tests/usecase`.

Imports must point inward: `http -> usecases -> domain <- infrastructure`.
The domain layer must stay free of framework and DB imports.

The repository ABCs in `src/domain/repositories.py` are a deliberate seam: usecases
depend on them, tests mock them (`AsyncMock(spec=...)`), Postgres adapters implement
them. Keep that seam; don't add new interfaces speculatively.

## Commands (run from `backend/`)

- `uv sync` — install dependencies (after `pyproject.toml` changes)
- `uv run pytest` — full suite (currently 21 tests; coverage is on via addopts)
- `uv run ruff check .` — lint
- `uv run ruff format .` — format (double quotes, 100 cols, enforces itself)
- `uv run python -m src.main` — dev server; env vars: `APP_HOST`, `APP_PORT`, `APP_RELOAD`
- `docker compose up --build` — postgres + liquibase migrations + backend (needs Docker)

Local DB credentials are the dev-only defaults in `docker-compose.yml` (`totem`/`totem`).
Config comes from env vars with sensible defaults (`APP_*`, `DATABASE_URL`).

Quality gate before committing: `uv run ruff check .` and `uv run pytest` must pass.

## Code style

- **Guard clauses and early returns**: validate inputs at the top of a method and
  raise/return immediately; avoid nested if/else chains. Example:
  `Cart.add_item` raises `ValueError("Quantity must be positive")` before doing any work.
- Money is `Decimal` in the domain; convert to `str` at the HTTP boundary only
  (see `ItemResponse.price` validator).
- State enums are `StrEnum`; persist `.value` to the DB (`order_type`, `order_status`,
  `payment_status`).
- Value objects are frozen dataclasses (`Item`); aggregates with state transitions are
  mutable dataclasses with explicit transition methods that raise `ValueError` on
  illegal transitions (`Order.mark_*`, `Order.cancel`).
- Repositories: `get_*` returns `None` when not found; `create`/`update`/`delete`
  raise `ValueError` when the aggregate has the wrong id state or 0 rows were affected.
- f-strings for interpolation.
- Async only where I/O happens: http, usecases (they await repos) and infrastructure
  are async; domain logic is synchronous.
- New async tests need no `@pytest.mark.asyncio` — `asyncio_mode = "auto"` is set
  (existing tests still carry the redundant decorator; don't add new ones).
- FastAPI wiring: use the `lifespan` context manager, not the deprecated
  `@app.on_event` (app.py still uses it; migrate when you touch it).

## Testing

- Usecase tests mock the repository ABC with `AsyncMock(spec=...Repository)`.
- Domain tests use plain dataclass instances.
- Coverage is on by default; `http/`, `schemas/`, `infrastructure/` are omitted from
  the report — they are meant to be covered by integration tests later, not unit tests.
- New behavior ships with tests.

## Git workflow

- Conventional Commits (`feat:`, `fix:`, `refactor:`, `chore:`).
- Work on a feature branch; open PRs with the gh CLI; merge via PR
  (history so far: `scaffold-initial-app` -> `main`).
- Keep `main` green (quality gate above).
