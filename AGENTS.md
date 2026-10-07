# AGENTS.md — Developer Environment & Agent Context

This repository is **Vitalcer**, a single-store dietetic store management system featuring a **FastAPI + SQLModel** backend and separated **SvelteKit static SPAs** (`apps/pos`, `apps/admin`) in a pnpm monorepo.

---

## 1. Environment & Package Access (`devenv.nix`)

All developer tools are provisioned hermetically via **Nix (`devenv.nix`)** and symlinked into `.devenv/profile/bin/`.

| Tool | Purpose | Primary Invocation |
| :--- | :--- | :--- |
| **`uv`** | Python 3.14 package & virtualenv manager | `uv run ...` / `uv add <pkg>` |
| **`ruff`** | Ultra-fast Python linter & formatter | `ruff check .` / `ruff format .` |
| **`ty`** | Astral's fast type checker (Rust) | `ty check` |
| **`basedpyright`**| Strict type checker & Python language server | `basedpyright` |
| **`biome`** | Ultra-fast JS/TS linter & formatter (Rust) | `biome check .` / `biome format --write .` |
| **`pnpm`** | Workspace package manager for frontend | `pnpm --filter <pkg> <cmd>` |
| **`postgresql_18`**| `psql`, `pg_dump`, and native database tools | `psql -U vitalcer -d vitalcer` |

### How to Run Commands
You have three reliable ways to execute commands:

1. **Via `make` (Recommended)**:  
   The `Makefile` forwards all commands directly to the hermetic devenv scripts in `.devenv/profile/bin`.
   ```bash
   make up          # Start all services concurrently (postgres, backend, admin, pos)
   make dev         # Run FastAPI backend with hot reload (host 0.0.0.0:8000)
   make dev-admin   # Run Admin SPA (host 0.0.0.0:5173)
   make dev-pos     # Run POS cashier SPA (host 0.0.0.0:5174)
   make db          # Start PostgreSQL (docker compose up -d postgres)
   make lint        # Run ruff check . && biome check .
   make fix         # Fix lint errors & auto-format (ruff + biome)
   make format      # Auto-format (ruff format . && biome format)
   make typecheck   # Fast type-check with ty
   make test        # Run pytest test suite
   make check       # Full validation: lint, format, typecheck, pytest, svelte-check & vitest
   make build       # Build all frontend SPAs (admin & pos)
   make openapi     # Export backend schema to scripts/openapi.json
   make codegen     # Export OpenAPI schema and regenerate @vitalcer/api client
   make codegen-watch # Watch server/ and continuously regenerate @vitalcer/api client
   ```
   > **Network Ports (WireGuard / Local)**:
   > - **FastAPI Backend**: `http://10.100.0.1:8000` (or `http://localhost:8000`)
   > - **Admin Backoffice**: `http://10.100.0.1:5173` (or `http://localhost:5173`)
   > - **Mobile POS**: `https://10.100.0.1:5174` (HTTPS via `basic-ssl`, required for phone camera `getUserMedia`)


2. **Via Devenv Scripts Directly**:
   All scripts defined in `devenv.nix` are available in `.devenv/profile/bin/` (or inside `devenv shell`):
   ```bash
   dev, dev-admin (or dev:admin), dev-pos (or dev:pos), db
   lint, fix, format (or :be / :fe)
   typecheck (ty), typecheck:strict (basedpyright)
   test (pytest), test:fe, test:all
   check (full monorepo), check:be, check:fe, check-admin, check-pos
   build, build-admin, build-pos
   openapi, codegen (or api:generate), codegen-watch (or codegen:watch)
   ```

3. **Prepend PATH in Shell Commands**:
   ```bash
   PATH="$PWD/.devenv/profile/bin:$PATH" check
   PATH="$PWD/.devenv/profile/bin:$PATH" uv run pytest
   PATH="$PWD/.devenv/profile/bin:$PATH" pnpm install
   ```

4. **Via `devenv shell`**:
   ```bash
   devenv shell <command>
   ```

---

## 2. Monorepo Structure

```
├── server/                     # FastAPI + SQLModel modular monolith backend
│   ├── main.py                 # FastAPI application factory & routers
│   ├── models/                 # SQLModel database tables (Product, User, InventoryLedger)
│   ├── schemas/                # Pydantic request/response validation schemas
│   ├── services/               # Business logic (inventory calculations, barcode parsing)
│   ├── core/                   # db.py (PostgreSQL / SQLite), config.py, dependencies.py
│   └── api/v1/                 # Endpoints (/products, /inventory, /users)
├── apps/
│   ├── pos/                    # Cashier counter SPA (SvelteKit static, barcode/keyboard-first)
│   └── admin/                  # Backoffice SPA (SvelteKit static, deliveries & cierre de caja)
├── packages/
│   ├── api/                    # Generated @hey-api client, Zod schemas, TanStack Query options
│   ├── ui/                     # Shared Tailwind CSS v4 & Bits UI / shadcn-svelte primitives
│   └── core/                  # EAN-13 embedded barcode parser, whole ARS & weight formatters
├── scripts/
│   └── api_export.py           # Exports backend OpenAPI spec to scripts/openapi.json
├── Makefile                    # Standard build & check targets (with .devenv in PATH)
├── devenv.nix                  # Nix toolchain definition
└── SPECIFICATION.md            # Deep system architecture & domain specification
```

---

## 3. Critical Rules for AI Agents

1. **Token Efficiency**: Do **NOT** read `SPECIFICATION.md` or large source trees upfront. Only consult `SPECIFICATION.md` on-demand when implementing domain rules (EAN-13 barcode parsing, double-entry inventory ledger movements, substitution workflows).
2. **Currency**: All prices are stored as **integers in whole Argentine Pesos (ARS)** (e.g. $1,500 ARS = `1500`). Cents/centavos are strictly omitted.
3. **Double-Entry Inventory**: Stock balances in `products` are never overwritten directly; all adjustments require an `InventoryLedger` entry (`quantity_delta`, `movement_type`, `balance_after`).
4. **Static SPAs**: Both frontend applications in `apps/` must remain pure static SPAs (`ssr = false`) with zero Node.js server dependencies in production.
5. **HTTPS & Camera Access**: `apps/pos` is served over **HTTPS** via `@vitejs/plugin-basic-ssl` on port `5174` because browsers enforce the W3C Secure Context rule for `navigator.mediaDevices.getUserMedia`. Do not downgrade it to plain HTTP.
6. **Tailwind CSS v4 `@source`**: All shared components in `packages/ui` must be explicitly discovered via `@source "./"` in `packages/ui/src/theme.css` so that Tailwind includes utilities from shared packages in the client CSS builds.
7. **Mobile-First Modals & Dialogs**: All modals in `@vitalcer/ui` must render through a portal with a backdrop overlay (`fixed inset-0 z-50 bg-black/60`), behave as a bottom sheet on mobile screens (`< sm`) with internal scrolling and fixed actions, and center on desktop viewports (`sm:`).
