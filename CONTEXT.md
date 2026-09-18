# Vitalcer Monorepo — Project Context

## Overview

This repository is a monorepo for **Vitalcer**, an e-commerce platform. It currently
contains a Python **FastAPI backend** (the only implemented component) and an empty
`apps/` workspace reserved for frontend applications via pnpm.

The API is branded **"Vitalcer API"** and describes itself as the backend for
"managing users, products, orders, and more". The users domain is the only domain
with a working implementation; products is scaffolded but not implemented.

- Python project name: `vitalcer-try2` (`pyproject.toml`), Python >= 3.14
- JS workspace name: `monorepo` (`package.json`), pnpm ^11.5.0
- API version: `1.0.0`, served under `/api` with versioned routers (`/api/v1`)

## Repository Layout

```
.
├── server/                     # FastAPI backend (current package name)
│   ├── main.py                 # App factory, metadata, router mounting
│   ├── api/v1/
│   │   ├── router.py           # /v1 aggregate router
│   │   └── endpoints/
│   │       ├── users.py        # Users CRUD endpoints
│   │       └── products.py     # Stub (empty)
│   ├── core/
│   │   ├── config.py           # Pydantic Settings (database_url, secret_key)
│   │   ├── db.py               # SQLAlchemy engine/session/Base
│   │   ├── dependencies.py     # get_db() FastAPI dependency
│   │   └── security.py         # Empty (no auth implemented)
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── users.py            # User model
│   │   └── products.py         # Broken stub
│   ├── schemas/                # Pydantic request/response models
│   │   ├── users.py            # UserBase / UserCreate / UserResponse
│   │   └── products.py         # Empty
│   ├── services/               # Business/data-access layer
│   │   ├── users_services.py   # get_users/get_user/create_user/delete_user
│   │   └── products_services.py# Empty
│   ├── utils/pagination.py     # Empty
│   └── data/db.here.md         # Placeholder for local DB files
├── apps/                       # Empty pnpm workspace (@see pnpm-workspace.yaml)
├── tests/
│   ├── conftest.py             # In-memory SQLite fixtures, DB override
│   ├── test_users_endpoints.py # API tests
│   └── test_users_services.py  # Service-layer tests
├── scripts/api_export.py       # Dumps OpenAPI schema to scripts/openapi.json
├── docker-compose.yaml         # PostgreSQL 18 (app/caddy commented out)
├── Caddyfile                   # Local HTTPS reverse proxy config (unused)
├── postgre.conf                # Tuned PostgreSQL 18 config (8 GB / 12 CPU)
├── Makefile                    # dev/lint/format/test/check/openapi targets
├── pyproject.toml              # Python deps, pytest, ruff, ty config
├── pyrightconfig.json          # Pyright excludes node_modules, __pycache__, apps
├── package.json / pnpm-*       # JS workspace scaffolding (no real packages yet)
└── uv.lock / .python-version   # uv lockfile, Python 3.14
```

Note: Git history and the last commit use the package name `app/`. The working tree
contains an **uncommitted rename `app/ → server/`** (see "Current State" below).

## Tech Stack

| Layer            | Choice                                                |
| ---------------- | ----------------------------------------------------- |
| Language         | Python 3.14 (`.python-version`, `requires-python`)     |
| Web framework    | FastAPI (`fastapi[standard] >= 0.136.1`)               |
| ORM              | SQLAlchemy 2.0 (declarative `Mapped`/`mapped_column`)  |
| Validation       | Pydantic v2 (via FastAPI); settings via pydantic-settings |
| DB driver        | psycopg 3 (PostgreSQL), sqlite3 (dev/test)             |
| Database         | PostgreSQL 18 (Docker) / SQLite (local + tests)         |
| Tests            | pytest 9 (`httpx`-based `TestClient`)                  |
| Lint/format      | Ruff (line length 88, rules `E`, `F`, `I`)             |
| Type checking    | mypy + `ty` (config in `pyproject.toml`, pyright config also present) |
| Package manager  | uv (Python), pnpm (JS workspace)                       |
| Infra            | Docker Compose, Caddy (local HTTPS), PostgreSQL config |

## Architecture

Strict layered flow, one module per concern and per domain:

```
HTTP request
  └─ FastAPI endpoint (server/api/v1/endpoints/*)
       ├─ Depends(get_db) → SQLAlchemy Session (server/core/dependencies.py)
       ├─ Pydantic schema validates input / serializes output (server/schemas/*)
       └─ Service function (server/services/*)
            └─ SQLAlchemy ORM model (server/models/*) → engine (server/core/db.py)
```

- **Endpoints** contain only HTTP concerns (status codes, 404s, docs metadata) and
  delegate all logic to services.
- **Services** own session usage and queries; `_user_select()` is the single base
  select, ready for `selectinload(...)` to prevent N+1 queries once relationships exist.
- **Models** map to DB tables; **schemas** never expose sensitive fields.
- **Tables are auto-created at import time** in `server/main.py:34` via
  `Base.metadata.create_all(bind=engine)`. There are no migrations (no Alembic).
- The OpenAPI schema can be exported with `make openapi`
  (`scripts/api_export.py` → `scripts/openapi.json`, gitignored).

## Domain: Users (implemented)

**Model** — `users` table (`server/models/users.py`):

| Column       | Type    | Notes                                        |
| ------------ | ------- | -------------------------------------------- |
| `id`         | Integer | PK, unique identifier                        |
| `username`   | String  | Indexed; **no unique constraint**            |
| `hashed_pass`| String  | Intended to be BCrypt-hashed (see gaps)      |

**Schemas** (`server/schemas/users.py`):

- `UserBase`: `username` (3–50 chars)
- `UserCreate`: adds `password` (8–128 chars)
- `UserResponse`: `id` + `username`; `from_attributes=True`; never returns password

**Endpoints** (`server/api/v1/endpoints/users.py`, all under `/api/v1/users`):

| Method   | Path            | Status | Operation ID  | Behavior                     |
| -------- | --------------- | ------ | ------------- | ---------------------------- |
| `GET`    | `/`             | 200    | `listUsers`   | List all users               |
| `GET`    | `/{user_id}`    | 200    | `getUser`     | Get one user, 404 if missing |
| `POST`   | `/`             | 201    | `createUser`  | Create user                  |
| `DELETE` | `/{user_id}`    | 204    | `deleteUser`  | Delete user, 404 if missing  |

**Service** (`server/services/users_services.py`): `get_users`, `get_user`,
`create_user`, `delete_user`. Duplicate usernames are currently allowed.

## Domain: Products (scaffolded, incomplete)

- `server/models/products.py` declares `Product` but only sets `__tablename__`; it
  also has a stray `from starlette.middleware.base import BaseHTTPMiddleware` and a
  bare `BaseHTTPMiddleware` statement in the class body. This is not valid model code.
- `server/api/v1/endpoints/products.py`, `server/schemas/products.py`, and
  `server/services/products_services.py` are empty, and the products router is not
  included in `server/api/v1/router.py`.
- `server/utils/pagination.py` and `server/core/security.py` are empty placeholders
  (pagination and auth were anticipated but never built).

## Data & Persistence

- `server/core/db.py` hardcodes `SQLALCHEMY_DATABASE_URL = "sqlite:///./app/data//test.db"`
  with `check_same_thread=False`. The path is **stale**: it still points at the
  pre-rename `app/` directory and contains a double slash.
- `SQLALCHEMY_DATABASE_URL` ignores `Settings.database_url`; `server/core/config.py`
  is currently never imported anywhere.
- `server/data/` is the intended home for local DB files (`db.here.md` placeholder).
- `postgre.conf` provides production-style tuning (2 GB shared buffers, 50 connections,
  SSD-oriented) for PostgreSQL 18.

## Configuration

`server/core/config.py` defines `Settings` (loaded from `.env`):

| Variable       | Required | Purpose                        |
| -------------- | -------- | ------------------------------ |
| `database_url` | yes      | Intended DB connection string  |
| `secret_key`   | yes      | Intended signing/auth secret   |
| `app_name`     | no       | Defaults to `"backend server"` |

`.env` is gitignored and currently absent; `.env.example` exists but is empty. Because
`Settings` is never instantiated, the app currently starts without these variables.

Environment expected by the commented-out app service in `docker-compose.yaml`:
`DATABASE_URL`, `SECRET_KEY`, `SUPERUSER_USERNAME`, `SUPERUSER_PASSWORD`.

## Development Workflow

Requires `uv` (Python) and `pnpm` (JS workspace).

```bash
make dev       # uv run uvicorn server.main:app --reload
make lint      # uv run ruff check .
make fix       # ruff check --fix
make format    # ruff format .
make test      # uv run pytest
make check     # ruff check . && pytest
make openapi   # export OpenAPI schema to scripts/openapi.json
```

Interactive API docs are served at `/docs` (Swagger) and `/redoc`.

## Testing

- `tests/conftest.py` builds a fresh **in-memory SQLite** engine per test with
  `StaticPool` (so all connections share one database), enables `PRAGMA foreign_keys=ON`,
  creates all tables, and overrides FastAPI's `get_db` dependency.
- `tests/test_users_services.py` covers service CRUD directly.
- `tests/test_users_endpoints.py` covers HTTP behavior: status codes, validation
  (422s), 404s, response shape, and that passwords/hashes are never exposed.
- Note: service tests document current behavior such as duplicate usernames being
  allowed and empty-string validation living in Pydantic, not the model.

## Deployment / Infrastructure

- `docker-compose.yaml` currently runs **only PostgreSQL 18-alpine** (`vitalcer`
  user/db/password) with a healthcheck and persistent volume. The `app` and `caddy`
  services are commented out.
- It mounts `./postgre.prod.conf`, but the repository only contains `postgre.conf`
  (mismatch to fix before deploying).
- `Caddyfile` is set up for local-network HTTPS (`local_certs`), long-lived caching
  for hashed assets and self-hosted fonts, reverse-proxying to `app:8000`, and
  Brotli/gzip/zstd compression. It assumes FastAPI serves the SPA/static fallback.
- `scripts/api_export.py` still has comments referencing the old `app` package.

## Current State & Known Gaps

The working tree is mid-refactor: the package was renamed from `app/` to `server/`
but that change is **not committed** (HEAD still contains `app/`; `server/` is
untracked and `app/` is deleted in the worktree). Consequences and open issues:

1. **Tests fail to run.** `pytest` aborts while loading `conftest.py` because
   `server/main.py` imports execute `Base.metadata.create_all(...)` against
   `sqlite:///./app/data//test.db`, and `app/data/` no longer exists →
   `sqlite3.OperationalError: unable to open database file`.
2. **Stale import in tests.** `tests/test_users_endpoints.py:3` imports
   `app.schemas.users` (should be `server.schemas.users`); Ruff flags it (`I001`).
3. **Products model is a broken stub** with a stray `BaseHTTPMiddleware` import/use;
   Ruff flags import sorting (`I001`).
4. **No auth/security.** `server/core/security.py` is empty; passwords are stored
   as-is in `hashed_pass` (tests even assert plaintext round-trips), despite the
   model comment saying BCrypt.
5. **No migrations.** Schema changes rely on `create_all`; no Alembic setup.
6. **Config is unused and drift-prone.** `database_url`/`secret_key` are required but
   never read; DB URL is hardcoded in `db.py`.
7. **Uniqueness missing.** `username` is indexed but not unique; duplicates allowed.
8. **Unimplemented domains.** Products/orders/pagination exist only as placeholders.
9. **Empty JS workspace.** `apps/` has no packages; root `package.json` is a stub.

## Conventions

- Python 3.14 typing (`Mapped[...]`, `X | None`, `Sequence[...]`), docstrings on
  models/services/endpoints.
- Ruff formatting, 88-char lines, import sorting enforced (`E`, `F`, `I`).
- Endpoints carry explicit `summary`, `description`, `response_description`, and
  stable `operation_id`s for clean generated clients.
- One service module per domain, named `<domain>_services.py`.
- No comments in code unless they add non-obvious value (the codebase follows this
  style closely); module/function docstrings are the norm.
- The `server/data/` directory is where local SQLite files belong.
