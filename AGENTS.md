# AGENTS.md — Developer Environment, System Architecture & Agent Rules

This repository is **Vitalcer**, a single-store dietetic store management system (*dietética*) handling **discrete unit goods** (packaged cookies, supplements, beverages) and **continuous bulk goods** (nuts, seeds, flours sold by weight with embedded-weight GS1 EAN-13 scale barcodes `20PPPPPWWWWWC`).

---

## 1. Tooling & Agent Update Invariant (STRICT)

> **Mandatory Rule for AI Agents**:
> Every time you touch or modify anything related to tooling (Nix, `devenv.nix`, packages, scripts, processes, ports, Docker, dev workflow, build configuration, linters, or proxies), you **MUST** record the change in the **Tooling & Infrastructure Ledger** (Section 6) of this file (`AGENTS.md`).
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

1. **Token Efficiency**: Do **NOT** read `SPECIFICATION.md` or large source trees upfront. Only consult `SPECIFICATION.md` on-demand for complex domain rules.
2. **Currency**: All prices are stored and calculated as **integers in whole Argentine Pesos (ARS)** (e.g. $1,500 ARS = `1500`). Cents/centavos are strictly forbidden.
3. **Double-Entry Inventory**: Stock balances in `products` are **never** overwritten directly; all adjustments require an immutable `InventoryLedger` entry (`quantity_delta`, `movement_type`, `balance_after`, `reference_id`).
4. **Static SPAs**: Both frontend applications in `apps/` must remain pure static SPAs (`ssr = false`, `@sveltejs/adapter-static`) with zero Node.js server dependencies in production.
5. **HTTPS & Camera Access**: `apps/pos` must be served over **HTTPS** (port `5174`) because browsers require a W3C Secure Context for `navigator.mediaDevices.getUserMedia`.
6. **Tailwind CSS v4 `@source`**: All shared components in `packages/ui` must be explicitly discovered via `@source "./"` in `packages/ui/src/theme.css`.
7. **Mobile-First Modals**: Modals in `@vitalcer/ui` render via portal with backdrop overlay (`fixed inset-0 z-50 bg-black/60`), behave as a bottom sheet on mobile (`< sm`) with internal scrolling and fixed actions, and center on desktop (`sm:`).

---

## 5. Implementation Status & Roadmap

- ✅ **Phase 1 (Data & Models)**: SQLModel database (`Product`, `User`, `InventoryLedger`), whole ARS integers, dual Postgres/SQLite test harness.
- ✅ **Phase 2 (Mobile POS Cashier)**: Barcode camera scanner with GPU detector, cart state machine in Svelte 5 runes, Web Audio tones, Cash change calculation & payment modal, atomic batch checkout committing to ledger (`movement_type = 'sale_pos'`).
- ✅ **Phase 3 (Inventory & Backoffice)**: Append-only double-entry engine (`/receive`, `/merma`, `/adjust`, `/reserve`, `/fulfill`, `/audit`), Admin catalog with `@tanstack/svelte-virtual` table, stock operations (`/actions`), ledger audit (`/ledger`), and sales dashboard (`/sales`).
- ⏳ **Phase 4A (Delivery Core & Mock Picking - Next)**: SQLModel tables (`DeliveryOrder`, `DeliveryOrderItem`), abstract `DeliveryAdapter`, virtual stock buffers & auto-pause, live picking UI (`/deliveries`) with acoustic alerts and v1 "Sin Stock / Quitar" removal switch, and mock simulation test harness.
- ⏳ **Phase 4B (Platform Integrations & Bureaucracy)**: Incremental real platform onboarding (one at a time per merchant credentials), webhooks, and v2 advanced substitution engine.
- ⏳ **Phase 5 (Financial Closing)**: Cierre de Caja (`/reports/cierre`), physical cash count (*Arqueo de caja*), daily shrinkage write-off.
- ✅ **Infrastructure**: Caddy reverse proxy integration (pre-compressed Level 11 Brotli/Gzip at build-time, automatic internal TLS, zero-CORS API proxying, HTTP/2 & HTTP/3).

---

## 6. Tooling & Infrastructure Ledger

| Date | Change Summary | Affected Components |
| :--- | :--- | :--- |
| **2026-10-07** | Unified `admin` and `pos` dev servers into `devenv up` via `processes` in `devenv.nix`. All 5 services (Postgres, FastAPI, Codegen watcher, Admin, POS) now start with a single `make up` / `devenv up`. | `devenv.nix`, `Makefile` |
| **2026-10-07** | Unified `CONTEXT.md` into `AGENTS.md`. Established strict tooling update invariant rule for AI agents. | `AGENTS.md`, `CONTEXT.md` |
| **2026-10-08** | Integrated Caddy 2 (`pkgs.caddy`) with automatic internal TLS (`tls internal`), zero-dependency build-time Brotli & Gzip pre-compression (`scripts/compress_static.mjs`), modular `Caddyfile` with snippets, and `make serve`. | `Caddyfile`, `devenv.nix`, `Makefile`, `scripts/compress_static.mjs`, `AGENTS.md` |
| **2026-10-08** | Removed `codegen` background watcher from `processes` in `devenv.nix`. Reduced `devenv up` background services from 5 to 4. OpenAPI client codegen is run on-demand via `make codegen` (or standalone `make codegen-watch`). | `devenv.nix`, `AGENTS.md` |
