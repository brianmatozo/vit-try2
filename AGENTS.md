# AGENTS.md — Developer Environment, System Architecture & Agent Rules

This repository is **Vitalcer**, a single-store dietetic store management system (*dietética*) handling **discrete unit goods** (packaged cookies, supplements, beverages) and **continuous bulk goods** (nuts, seeds, flours sold by weight with embedded-weight GS1 EAN-13 scale barcodes `20PPPPPWWWWWC`).

---

## 1. Tooling & Agent Update Invariant (STRICT)

> **Mandatory Rules for AI Agents**:
> 1. **Infrastructure Ledger**: Every time you touch or modify anything related to tooling (Nix, `devenv.nix`, packages, scripts, processes, ports, Docker, dev workflow, build configuration, linters, or proxies), you **MUST** record the change in the **Tooling & Infrastructure Ledger** (Section 8) of this file (`AGENTS.md`).
> 2. **Zero Unconfirmed Paid/Billable API Calls**: AI agents are strictly forbidden from executing scripts, tests, or commands that make live calls to external billable APIs (e.g. OpenRouter, LLM endpoints, paid cloud services) using user credentials without explicit, unambiguous user consent in chat. Always use `--mock` mode, offline fixtures, or unit tests. Never spend user money autonomously.
> Furthermore, this file is the **single, super-compressed technical source of truth** for project architecture, commands, directories, domain invariants, and live status. Keep it concise, high-density, and LLM-friendly.

---

## 2. Environment, Ports & Unified Process Execution

All developer tools are provisioned hermetically via **Nix (`devenv.nix`)** into `.devenv/profile/bin/`.

### Network Ports & Topology
| Service | Local / WireGuard URL | Port | Protocol & Notes |
| :--- | :--- | :--- | :--- |
| **PostgreSQL 18** | `localhost:5432` | `5432` | Native devenv service (`vitalcer:vitalcer@localhost:5432/vitalcer`) |
| **FastAPI Backend** | `http://localhost:8000` (`http://10.100.0.1:8000`) | `8000` | HTTP / REST API (`/api/v1`) |
| **Admin Backoffice** | `http://localhost:5173` (`http://10.100.0.1:5173`) | `5173` | HTTP (Static SPA via Vite) |
| **Mobile POS App** | `https://localhost:5174` (`https://10.100.0.1:5174`) | `5174` | **HTTPS** (`basic-ssl` required for phone camera `getUserMedia`) |

### Unified Process Execution (`devenv up`)
`devenv up` (and `make up`) manages **ALL 4 services concurrently** via `process-compose`:
1. `postgres`: PostgreSQL 18 native service
2. `server`: FastAPI with hot reload (`uvicorn server.main:app --reload --host 0.0.0.0 --port 8000`)
3. `admin`: Admin Backoffice SPA (`pnpm --filter admin dev`)
4. `pos`: Cashier Counter SPA (`pnpm --filter pos dev`)

### Primary Developer Commands
```bash
make up          # Start all 4 services concurrently (postgres, server, admin, pos)
make dev         # Run FastAPI backend in isolation (0.0.0.0:8000)
make dev-admin   # Run Admin SPA in isolation (0.0.0.0:5173)
make dev-pos     # Run Mobile POS SPA in isolation (0.0.0.0:5174, HTTPS)
make db          # Start Docker PostgreSQL fallback
make lint        # Run ruff check . && biome check .
make fix         # Fix lint errors & format (ruff + biome)
make format      # Auto-format (ruff format . && biome format)
make typecheck   # Fast typecheck (ty check)
make test        # Run pytest test suite (SQLite in-memory test harness)
make check       # Full validation: ruff, ty, pytest, codegen, biome, svelte-check, vitest
make build       # Prerender, build all frontend static SPAs, & precompress (Brotli/Gzip)
make serve       # Build & serve production SPAs via Caddy (port 5173 & HTTPS 5174)
make caddy-validate # Validate Caddyfile configuration syntax
make caddy-reload   # Hot-reload Caddy without dropping active connections
make openapi     # Export backend OpenAPI schema to scripts/openapi.json
make codegen     # Export OpenAPI & regenerate @vitalcer/api client
```

---

## 3. Monorepo Structure

```text
├── server/                     # FastAPI + SQLModel modular monolith backend
│   ├── main.py                 # FastAPI application factory & routers
│   ├── api/v1/endpoints/       # users.py, products.py, inventory.py
│   ├── models/                 # SQLModel tables (Product, User, InventoryLedger)
│   ├── schemas/                # Pydantic request/response validation schemas
│   ├── services/               # Business logic (inventory calculations, barcode parsing)
│   ├── core/                   # db.py (PostgreSQL / SQLite), config.py, dependencies.py
│   └── utils/barcode.py        # GS1 scale embedded-weight barcode parser
├── apps/
│   ├── pos/                    # Mobile Cashier Counter SPA (SvelteKit static, HTTPS port 5174)
│   │   ├── src/lib/camera/     # Dual-engine barcode scanner (native BarcodeDetector + ZXing fallback)
│   │   ├── src/lib/cart/       # Cart state machine in Svelte 5 Runes ($state, discrete & bulk ARS)
│   │   ├── src/lib/checkout/   # Cash (change calc), Card, QR MP checkout modal committing batch sales
│   │   └── src/lib/audio/      # Web Audio scanner beeps & buzzer error tones
│   └── admin/                  # Operations & Backoffice SPA (SvelteKit static, port 5173)
│       ├── src/routes/         # Catalog with 60 FPS @tanstack/svelte-virtual table & product editor
│       ├── src/routes/sales/   # POS sales dashboard (KPI cards, grouped tickets, itemized receipts)
│       ├── src/routes/actions/ # Stock replenishment, shrinkage merma logging, manual adjustments
│       └── src/routes/ledger/  # Double-entry inventory audit ledger with filters
├── packages/
│   ├── api/                    # Centralized @hey-api client, Zod schemas, TanStack Query options
│   ├── ui/                     # Shared Tailwind CSS v4 tokens (@source enabled) & Bits UI primitives
│   └── core/                   # EAN-13 embedded barcode parser, whole ARS & weight formatters
├── scripts/
│   ├── api_export.py           # OpenAPI exporter
│   └── compress_static.mjs     # Build-time Level 11 Brotli & Gzip pre-compression
├── Caddyfile                   # High-speed reverse proxy & static SPA server (internal TLS & Brotli)
├── Makefile                    # Make targets forwarding to .devenv/profile/bin
├── devenv.nix                  # Hermetic Nix environment & process-compose runner
└── SPECIFICATION.md            # Deep system architecture & domain specification (read on-demand only)
```

---

## 4. Critical Architecture & Domain Invariants

1. **Token Efficiency**: Do NOT read `SPECIFICATION.md` or large source trees upfront. Only consult documentation on-demand for specific domain logic.
2. **Currency**: All prices are stored and calculated as **integers in whole Argentine Pesos (ARS)** (e.g. $1,500 ARS = `1500`). Cents/centavos are strictly forbidden.
3. **Double-Entry Inventory**: Stock balances in `products` are never overwritten directly; all adjustments require an immutable `InventoryLedger` entry (`quantity_delta`, `movement_type`, `balance_after`, `reference_id`).
4. **Static SPAs**: Both frontend applications in `apps/` must remain pure static SPAs (`ssr = false`, `@sveltejs/adapter-static`) with zero Node.js server dependencies in production.
5. **HTTPS & Camera Access**: `apps/pos` must be served over HTTPS (port `5174`) for W3C Secure Context camera permissions (`navigator.mediaDevices.getUserMedia`).
6. **Tailwind CSS v4 & Token Architecture**:
   - App CSS entry files (`apps/*/src/routes/layout.css`) must declare `@source "../../../../packages/ui/src";`.
   - `packages/ui/src/theme.css` is the single source of truth for design tokens (`@theme`, `@utility`). Never import Tailwind directly inside it.
   - **Zero Arbitrary Brackets**: Do NOT use arbitrary bracket utilities (e.g., `text-[10px]`, `h-[40px]`). Dense POS typography and clamps must use tokens defined in `@theme` (e.g. `--text-2xs: 10px;`, `--text-3xs: 9px;`).
7. **Mobile-First Modals**: Modals in `@vitalcer/ui` render via portal with backdrop overlay (`fixed inset-0 z-50 bg-black/60`), behave as a bottom sheet on mobile (`< sm`), and center on desktop (`sm:`). For alerts or modals that must always center on all screens, pass `position="center"` or `centered`. Dialog footer buttons render in a `justify-end` container; use `mr-auto` (not `ml-auto`) to left-align footer actions.
8. **Zero Autonomous Paid API Calls**: AI agents must NEVER execute scripts or commands that make live requests to external paid APIs using user credentials without explicit chat consent. Always use `--mock` mode, fixtures, or local SQLite mocks.

---

## 6. Backend Architecture & Async SQLModel Contract

### A. Module Boundaries & Routing Invariant

The backend is organized into vertical domain slices under `server/modules/`. Cross-cutting infrastructure lives strictly in `server/core/`.

```text
server/
├── core/                        # Cross-cutting infrastructure ONLY
│   ├── config.py                # Pydantic Settings & environment variables
│   ├── db.py                    # async_engine (psycopg / aiosqlite), AsyncSessionLocal, get_async_db
│   ├── dependencies.py          # Auth validation, permission dependencies
│   └── exceptions.py            # Global HTTP & domain exception handlers
├── modules/
│   ├── catalog/                 # Product domain
│   │   ├── models.py            # SQLModel table: Product
│   │   ├── schemas.py           # Request/response Pydantic models
│   │   ├── router.py            # APIRouter(prefix="/products", tags=["catalog"])
│   │   ├── service.py           # Product catalog queries & mutations
│   │   └── barcode.py           # GS1 scale embedded barcode parser (20PPPPPWWWWWC)
│   ├── inventory/               # Double-entry ledger domain
│   │   ├── models.py            # SQLModel tables: StockItem, InventoryLedger
│   │   ├── schemas.py           # Movement payloads (Receive, Adjust, Merma, Fulfill)
│   │   ├── router.py            # APIRouter(prefix="/inventory", tags=["inventory"])
│   │   ├── engine.py            # Atomic transaction mutation engine (OCC & ledger append)
│   │   └── queries.py           # Point-in-time stock audit, reconciliation, and valuations
│   └── identity/                # Authentication & User Management
│       ├── models.py            # SQLModel table: User
│       ├── schemas.py           # Login, profile, and role schemas
│       ├── router.py            # APIRouter(prefix="/users", tags=["identity"])
│       └── service.py           # Password hashing & JWT token issuance
├── api/
│   └── v1/
│       └── router.py            # Explicit aggregate router (includes catalog, inventory, identity)
└── main.py                      # FastAPI lifespan (metadata.create_all), app factory, mount /api/v1
```

* **Explicit Routing Only**: Do NOT use dynamic reflection or filesystem-scanning router libraries. Each domain module exports a standard `router = APIRouter(...)`. Routers are imported and wired explicitly in `server/api/v1/router.py`:
  ```python
  from fastapi import APIRouter
  from server.modules.catalog.router import router as catalog_router
  from server.modules.identity.router import router as identity_router
  from server.modules.inventory.router import router as inventory_router

  v1_router = APIRouter(prefix="/v1")
  v1_router.include_router(identity_router)
  v1_router.include_router(catalog_router)
  v1_router.include_router(inventory_router)
  ```

* **Strict Dependency Flow**: `core/` must NEVER import from `modules/`. Modules may import from `core/`. Modules must not import models directly from each other; reference foreign keys by table name strings (e.g., `foreign_key="products.id"`).

### B. The 250 LOC Backend Blueprint

No single Python file under `server/` may exceed **250 lines of code**. When a file approaches this threshold:
* **Split Read/Write Paths**: Monolithic services must be split into a mutation engine (`engine.py`) and a read/reporting service (`queries.py`).
* **Extract Query Builders**: Complex SQL joins or aggregations belong in dedicated helper functions inside `queries.py`, never inline in endpoints.
* **Thin Routers**: Routers are pure HTTP coordinators. Endpoints parse request models, call service/engine functions, translate domain exceptions to HTTP status codes, and return response schemas. Zero business logic or raw SQL execution inside `router.py`.

### C. Async MVCC & Double-Entry Ledger Invariants

* **Zero Direct Balance Overwrites**:
  * Stock balances in `products` or `stock_items` are NEVER overwritten directly via standalone `UPDATE` statements.
  * Every physical stock variation must occur through an append-only `InventoryLedger` row (`quantity_delta`, `movement_type`, `balance_after`, `version_nonce`, `reference_id`).
* **Append-Only Immutability**:
  * Ledger rows are immutable. The ORM and application code must never issue `UPDATE` or `DELETE` queries on `InventoryLedger`.
  * Stock corrections must take the form of compensating ledger entries (`ADJUST` or `MERMA`).
* **Concurrency Control & Atomic Mutations**:
  * Stock updates must run inside an explicit transaction context using either row locking (`select(...).with_for_update()`) or Optimistic Concurrency Control (OCC) via a version column:
    ```python
    async with session.begin():
        stock = (
            await session.exec(
                select(StockItem).where(StockItem.product_id == product_id).with_for_update()
            )
        ).one_or_none()

        # Mutate aggregate & append immutable ledger entry within the same atomic commit
        ...
    ```
  * Never calculate stock balances in Python memory across uncommitted, non-locking reads.
  * Ledger insertion and aggregate balance modification must happen within the exact same database transaction. Partial commits are strictly forbidden.

### D. Async Session & Lifespan Invariants

* **Async Session Lifecycle**:
  * Endpoints must consume database sessions exclusively through `session: AsyncSession = Depends(get_async_db)`.
  * Sessions are configured with `expire_on_commit=False`. Never call `session.refresh()` unless the database generates server-side defaults required immediately in the HTTP response.
  * Never instantiate ad-hoc `AsyncSession` instances inside domain services or background tasks without guaranteeing disposal via an async context manager.
* **Startup Metadata Registration (`create_all`)**:
  * Because tables are created dynamically on startup via `conn.run_sync(Base.metadata.create_all)`, all SQLModel table classes must be imported into the application scope before the lifespan runs.
  * Ensure `server/models/__init__.py` or the module routers explicitly import all table models so `SQLModel.metadata` is fully populated when `create_all` executes.
* **Dual Engine Dialect Compatibility**:
  * All code must execute cleanly on both PostgreSQL (`postgresql+psycopg://` via psycopg 3) and SQLite (`sqlite+aiosqlite:///`).
  * Do NOT use Postgres-exclusive dialect types (such as `JSONB` or `ARRAY`) without standard fallback representations. SQLite compatibility must be preserved for rapid local testing.
  * Always store timestamps as timezone-aware UTC: `datetime.now(timezone.utc)`.

### E. Currency, Barcode & Data Invariants

* **Whole ARS Integer Currency**:
  * All prices, costs, line totals, and order amounts must be stored and processed as integers in whole Argentine Pesos (ARS) (`int`).
  * Never use `float` or `Decimal` for currency columns or schemas.
  * If a discount or unit conversion yields a fractional value, it must be explicitly rounded to the nearest whole integer (`round()`) before validation and persistence.
* **GS1 Barcode Validation**:
  * GS1 embedded-weight barcodes (`20PPPPPWWWWWC`) must be parsed and verified via checksum before being accepted by catalog or inventory movement endpoints.
  * Parsed scale weights must be positive floats with fixed 3-decimal precision (grams/kilograms).

### F. Verification Gates

Before declaring any backend feature, endpoint, or refactor complete, the following gates must execute and pass without error:

1. `uv run ruff check .` (zero linting or syntax errors)
2. `uv run ruff format --check .` (standard formatting compliance)
3. `uv run basedpyright` (zero type-check errors across models, schemas, and engines)
4. `uv run pytest` (100% passing tests across atomic ledger transactions, balance constraints, and endpoints)
5. `uv run python scripts/api_export.py` (OpenAPI spec re-exported cleanly to keep `@vitalcer/api` in sync)

---

## 7. Implementation Status & Roadmap

- ✅ **Phase 1 (Data & Models)**: SQLModel database (`Product`, `User`, `InventoryLedger`), whole ARS integers, dual Postgres/SQLite test harness.
- ✅ **Phase 2 (Mobile POS Cashier)**: Barcode camera scanner with GPU detector, cart state machine in Svelte 5 runes, Web Audio tones, Cash change calculation & payment modal, atomic batch checkout committing to ledger (`movement_type = 'sale_pos'`).
- ✅ **Phase 3 (Inventory & Backoffice)**: Append-only double-entry engine (`/receive`, `/merma`, `/adjust`, `/reserve`, `/fulfill`, `/audit`), Admin catalog with `@tanstack/svelte-virtual` table, stock operations (`/actions`), ledger audit (`/ledger`), and sales dashboard (`/sales`).
- ⏳ **Phase 3B (Remito Ingestion & Automated Stock Inbound)**: Vision AI pipeline (Gemini 2.0 Flash via OpenRouter) for physical delivery receipts (*Recibo X* / *Remitos*), packaging-to-unit converter, Argentine fiscal split calculator (60/40 blanco/negro + 21% IVA), staging UI (`/remitos`), and alias cache (`supplier_product_mappings`). Full spec: [`docs/remito_ingestion_specification.md`](docs/remito_ingestion_specification.md).
- ⏳ **Phase 4A (Delivery Core & Mock Picking - Next)**: SQLModel tables (`DeliveryOrder`, `DeliveryOrderItem`), abstract `DeliveryAdapter`, virtual stock buffers & auto-pause, live picking UI (`/deliveries`) with acoustic alerts and v1 "Sin Stock / Quitar" removal switch, and mock simulation test harness.
- ⏳ **Phase 4B (Platform Integrations & Bureaucracy)**: Incremental real platform onboarding (one at a time per merchant credentials), webhooks, and v2 advanced substitution engine.
- ⏳ **Phase 5 (Financial Closing)**: Cierre de Caja (`/reports/cierre`), physical cash count (*Arqueo de caja*), daily shrinkage write-off.
- ✅ **Infrastructure**: Caddy reverse proxy integration (pre-compressed Level 11 Brotli/Gzip at build-time, automatic internal TLS, zero-CORS API proxying, HTTP/2 & HTTP/3).

---

## 8. Tooling & Infrastructure Ledger

| Date | Change Summary | Affected Components |
| :--- | :--- | :--- |
| **2026-10-07** | Unified `admin` and `pos` dev servers into `devenv up` via `processes` in `devenv.nix`. All 5 services (Postgres, FastAPI, Codegen watcher, Admin, POS) now start with a single `make up` / `devenv up`. | `devenv.nix`, `Makefile` |
| **2026-10-07** | Unified `CONTEXT.md` into `AGENTS.md`. Established strict tooling update invariant rule for AI agents. | `AGENTS.md`, `CONTEXT.md` |
| **2026-10-08** | Integrated Caddy 2 (`pkgs.caddy`) with automatic internal TLS (`tls internal`), zero-dependency build-time Brotli & Gzip pre-compression (`scripts/compress_static.mjs`), modular `Caddyfile` with snippets, and `make serve`. | `Caddyfile`, `devenv.nix`, `Makefile`, `scripts/compress_static.mjs`, `AGENTS.md` |
| **2026-10-08** | Removed `codegen` background watcher from `processes` in `devenv.nix`. Reduced `devenv up` background services from 5 to 4. OpenAPI client codegen is run on-demand via `make codegen` (or standalone `make codegen-watch`). | `devenv.nix`, `AGENTS.md` |
| **2026-10-09** | Enabled project documentation tracking by removing blanket `docs/` exclusion in `.gitignore`, retaining `docs/_build/` for build artifacts. | `.gitignore`, `AGENTS.md` |
| **2026-10-09** | Added strict invariant forbidding AI agents from autonomously making live calls to external billable APIs (OpenRouter/LLM endpoints). | `AGENTS.md` |
| **2026-10-12** | Migrated Svelte MCP server to project-local configurations (`.agents/mcp_config.json`, `opencode.json`). Configured on-demand (disabled by default) MCP servers for Python analyzer, Context7 documentation, and Microsoft PostgreSQL across `.agents/mcp_config.json`, workspace plugin `.agents/plugins/vitalcer/`, and `opencode.json`. | `.agents/mcp_config.json`, `.agents/plugins/vitalcer/`, `opencode.json`, `AGENTS.md` |
| **2026-10-13** | Built XAMPP-style Windows distribution & Desktop Control Panel (PostgreSQL 18 supervisor, FastAPI, Caddy, Tkinter GUI `vitalcer_control.py`, automated `install.bat`/`install.ps1`, and documentation `docs/WINDOWS_SETUP.md`). Relaxed Python requirement to `>=3.12`. | `scripts/windows/`, `pyproject.toml`, `docs/WINDOWS_SETUP.md`, `AGENTS.md` |
| **2026-10-13** | Standardized monorepo frontend (aligned Zod 3, pruned unused deps in apps, added `"svelte"` export map to `@vitalcer/ui`, fixed Tailwind v4 `@source` scanner from apps into `packages/ui`, and enhanced `Dialog` centered positioning). | `packages/ui/`, `apps/pos/`, `apps/admin/`, `AGENTS.md` |
| **2026-10-14** | Synchronized devenv 2.4.0 lockfile, configured `pass` in `services.postgres.initialDatabases`, pruned redundant `postgresql_18` from `packages` (benefiting from PostgreSQL binary-only shell isolation), updated Biome schema to 2.5.15, and relaxed pnpm `devEngines` for NixOS. | `devenv.nix`, `devenv.lock`, `biome.json`, `package.json`, `AGENTS.md` |
| **2026-10-15** | Fixed Windows automation & PostgreSQL runner: added auto-download of portable PostgreSQL 18 into `tools/pgsql`, automatic `vitalcer` DB creation, console UTF-8 reconfigure to prevent emoji charmap errors, WindowsSelectorEventLoopPolicy for async psycopg3, and added `tools/`, `data/`, `server/data/` to `.gitignore`. | `scripts/windows/`, `server/core/db.py`, `.gitignore`, `AGENTS.md` |
| **2026-10-16** | Added Windows Inno Setup installer pipeline (`vitalcer.iss`, `package.ps1`/`package.bat`, `vitalcer.spec`), dual-mode backend execution in `vitalcer_control.py`, frozen app path resolution in `service_manager.py`, accelerated portable PostgreSQL download, and `data/logs` auto-provisioning. | `scripts/windows/`, `pyproject.toml`, `docs/WINDOWS_SETUP.md`, `.gitignore`, `AGENTS.md` |
| **2026-10-25** | Added Vitest to `apps/admin` devDependencies (`vitest ^3.0.0`) and configured `"test": "vitest run"` script for unit testing catalog TypeScript & rune modules. | `apps/admin/package.json`, `AGENTS.md` |
| **2026-10-25** | Added Vitest to `apps/pos` devDependencies (`vitest ^3.0.0`) and configured `"test": "vitest run"` script for unit testing camera & POS rune modules. | `apps/pos/package.json`, `AGENTS.md` |
