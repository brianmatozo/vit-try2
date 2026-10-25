# AGENTS.md — Developer Environment, System Architecture & Agent Rules

This repository is **Vitalcer**, a single-store dietetic store management system (*dietética*) handling **discrete unit goods** (packaged cookies, supplements, beverages) and **continuous bulk goods** (nuts, seeds, flours sold by weight with embedded-weight GS1 EAN-13 scale barcodes `20PPPPPWWWWWC`).

---

## 1. Tooling & Agent Update Invariant (STRICT)

> **Mandatory Rules for AI Agents**:
> 1. **Infrastructure Ledger**: Every time you touch or modify anything related to tooling (Nix, `devenv.nix`, packages, scripts, processes, ports, Docker, dev workflow, build configuration, linters, or proxies), you **MUST** record the change in the **Tooling & Infrastructure Ledger** (Section 6) of this file (`AGENTS.md`).
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

```
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
* App CSS entry files (`apps/*/src/routes/layout.css`) must declare `@source "../../../../packages/ui/src";`.
* `packages/ui/src/theme.css` is the single source of truth for design tokens (`@theme`, `@utility`). Never import Tailwind directly inside it.
* **Zero Arbitrary Brackets**: Do NOT use arbitrary bracket utilities (e.g., `text-[10px]`, `h-[40px]`). Dense POS typography and clamps must use tokens defined in `@theme` (e.g. `--text-2xs: 10px;`, `--text-3xs: 9px;`).


7. **Mobile-First Modals**: Modals in `@vitalcer/ui` render via portal with backdrop overlay (`fixed inset-0 z-50 bg-black/60`), behave as a bottom sheet on mobile (`< sm`), and center on desktop (`sm:`). For alerts or modals that must always center on all screens, pass `position="center"` or `centered`. Dialog footer buttons render in a `justify-end` container; use `mr-auto` (not `ml-auto`) to left-align footer actions.
8. **Zero Autonomous Paid API Calls**: AI agents must NEVER execute scripts or commands that make live requests to external paid APIs using user credentials without explicit chat consent. Always use `--mock` mode, fixtures, or local SQLite mocks.

---

## 5. Workspace Boundaries & Svelte 5 Architecture Contract

### A. Package & Layer Boundaries

* **`@vitalcer/core` (Domain Math & Invariants)**: Framework-agnostic pure TypeScript. GS1 barcode parsing, ARS integer currency math, and weight calculation logic. Must have zero DOM/browser dependencies and run cleanly in Node/Vitest.
* **`@vitalcer/ui` (Design System Primitives)**: Generic, unstyled/Tailwind-styled UI primitives (Bits UI wrappers: Dialog, Button, Card, Input) and design tokens (`theme.css`). Must contain **zero domain knowledge** (no products, prices, barcodes, or cart types).
* **`@vitalcer/api` (Network & Contracts)**: OpenAPI-generated client, Zod validation schemas, and TanStack Query option factories.
* **`apps/*/src/lib/<domain>/` (App-Specific Features)**: State machines, browser APIs (audio synthesis, WebRTC camera streams), table column layouts, and domain view components.

### B. Directory & Routing Invariant

* **Routes are Pure Coordinators**: `apps/*/src/routes/` is strictly reserved for SvelteKit routing artifacts (`+page.svelte`, `+layout.svelte`, `+layout.ts`, `layout.css`).
* **Zero Route-Adjacent Helpers**: Never create helper scripts, `.svelte.ts` files, or subcomponent folders inside `src/routes/**/`. All feature logic and subcomponents must live under `apps/*/src/lib/<domain>/`.

### C. The 250 LOC Feature Blueprint

No `.svelte` or `.svelte.ts` file may exceed **250 lines of code**. When decomposing bloated files or adding features, organize the target domain under `apps/<app>/src/lib/<domain>/`:

```
src/lib/<domain>/
├── <feature>-filter.ts         # Pure domain functions & metrics (no UI, tested via Vitest)
├── <feature>-filter.test.ts    # Unit tests for domain calculations
├── columns.ts                  # TanStack table column definitions (if tabular data)
├── <feature>.svelte.ts         # Svelte 5 runes controller class ($state, $derived, validation)
├── <feature>.test.ts           # Unit tests for state machine transitions
└── components/                 # Presentational leaves (< 150 LOC each)
    ├── <Feature>Header.svelte
    └── <Feature>Dialog.svelte

```

### D. Svelte 5 Runes & Import Rules

1. **Extension Dropping on `.svelte.ts` Imports**: When importing `.svelte.ts` modules into `.svelte` or `.ts` files, omit the `.ts` extension:
```typescript
// Correct
import { ProductFormState } from '$lib/catalog/product-form.svelte';

// WRONG - will cause bundler resolution errors
import { ProductFormState } from '$lib/catalog/product-form.svelte.ts';

```


2. **State Lifecycle Patterns**:
* **Ephemeral / Local State (Forms, Modals)**: Export an uninstantiated class (`export class ProductFormState { ... }`). The consuming component instantiates it: `const form = new ProductFormState()`.
* **Persistent / Global State (POS Cart)**: Export a class alongside a shared singleton instance (`export const cart = new CartState()`).



### E. Styling Standards & Scoped CSS

* **Utility Discipline**: Never chain more than 4–5 utility classes on a single HTML tag. Keep markup clean, readable, and structural.
* **Component-Scoped `<style>**`: For complex internal component layouts, animations, or responsive variant blocks, use native Svelte `<style>` tags at the bottom of the file rather than 100-character utility strings.
* **Shared Primitives & `class` Merging**: All components in `@vitalcer/ui` must accept an optional `class` prop and merge via `cn()`, imported strictly from `@vitalcer/ui`.

### F. Verification Gates

Before declaring any frontend change or refactor complete, run and pass:

1. `pnpm svelte-check` (zero TypeScript and Svelte warnings)
2. `pnpm vitest run` (all unit tests passing)
3. `pnpm biome check` (formatting and lint compliance)
4. Production build (`make check` or static adapter build)

---

## 6. Implementation Status & Roadmap

- ✅ **Phase 1 (Data & Models)**: SQLModel database (`Product`, `User`, `InventoryLedger`), whole ARS integers, dual Postgres/SQLite test harness.
- ✅ **Phase 2 (Mobile POS Cashier)**: Barcode camera scanner with GPU detector, cart state machine in Svelte 5 runes, Web Audio tones, Cash change calculation & payment modal, atomic batch checkout committing to ledger (`movement_type = 'sale_pos'`).
- ✅ **Phase 3 (Inventory & Backoffice)**: Append-only double-entry engine (`/receive`, `/merma`, `/adjust`, `/reserve`, `/fulfill`, `/audit`), Admin catalog with `@tanstack/svelte-virtual` table, stock operations (`/actions`), ledger audit (`/ledger`), and sales dashboard (`/sales`).
- ⏳ **Phase 3B (Remito Ingestion & Automated Stock Inbound)**: Vision AI pipeline (Gemini 2.0 Flash via OpenRouter) for physical delivery receipts (*Recibo X* / *Remitos*), packaging-to-unit converter, Argentine fiscal split calculator (60/40 blanco/negro + 21% IVA), staging UI (`/remitos`), and alias cache (`supplier_product_mappings`). Full spec: [`docs/remito_ingestion_specification.md`](docs/remito_ingestion_specification.md).
- ⏳ **Phase 4A (Delivery Core & Mock Picking - Next)**: SQLModel tables (`DeliveryOrder`, `DeliveryOrderItem`), abstract `DeliveryAdapter`, virtual stock buffers & auto-pause, live picking UI (`/deliveries`) with acoustic alerts and v1 "Sin Stock / Quitar" removal switch, and mock simulation test harness.
- ⏳ **Phase 4B (Platform Integrations & Bureaucracy)**: Incremental real platform onboarding (one at a time per merchant credentials), webhooks, and v2 advanced substitution engine.
- ⏳ **Phase 5 (Financial Closing)**: Cierre de Caja (`/reports/cierre`), physical cash count (*Arqueo de caja*), daily shrinkage write-off.
- ✅ **Infrastructure**: Caddy reverse proxy integration (pre-compressed Level 11 Brotli/Gzip at build-time, automatic internal TLS, zero-CORS API proxying, HTTP/2 & HTTP/3).

---

## 7. Tooling & Infrastructure Ledger

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
