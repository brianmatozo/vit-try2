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
   The `Makefile` automatically prepends `.devenv/profile/bin` to `PATH`.
   ```bash
   make dev         # Run FastAPI backend with hot reload
   make lint        # Run ruff check .
   make fix         # Fix lint errors & auto-format
   make format      # Format with ruff
   make typecheck   # Type-check with ty
   make test        # Run pytest test suite
   make openapi     # Export backend schema to scripts/openapi.json
   ```

2. **Prepend PATH in Shell Commands**:
   ```bash
   PATH="$PWD/.devenv/profile/bin:$PATH" uv run pytest
   PATH="$PWD/.devenv/profile/bin:$PATH" pnpm install
   ```

3. **Via `devenv shell`**:
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
