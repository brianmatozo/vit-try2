# Vitalcer Monorepo — Project Context

> **Note for AI Agents**: For immediate developer environment instructions and toolchain execution, see [AGENTS.md](AGENTS.md). For deep technical specifications and domain rules, see [SPECIFICATION.md](SPECIFICATION.md).

---

## 1. Overview

**Vitalcer** is a single-store dietetic store management system (*dietética*) handling both **discrete unit goods** (packaged cookies, supplements, beverages) and **continuous bulk goods** (nuts, seeds, flours, dried fruit sold by grams with embedded-weight EAN-13 scale barcodes) alongside multi-platform delivery fulfillment (**PedidosYa, Rappi, VGO, MercadoLibre**).

- **Architecture**: Modular Monolith backend paired with decoupled static SvelteKit SPAs.
- **Backend**: Python >= 3.14, FastAPI, SQLModel, FastCRUD (`server/`).
- **Frontend**: Svelte 5 (Runes), SvelteKit static SPAs (`apps/pos`, `apps/admin`), TanStack Suite (`Query`, `Table`, `Virtual`), Tailwind CSS v4, Bits UI / shadcn-svelte (`apps/*`, `packages/*`).
- **Toolchain**: Hermetic Nix via `devenv.nix` (`uv`, `ruff`, `ty`, `basedpyright`, `biome`, `pnpm`, `postgresql_18`).
- **Database**: PostgreSQL 18 (production/docker) / SQLite in-memory (isolated test suite).

---

## 2. Network Topology & Ports

| Service | Local / WireGuard URL | Port | Protocol & Notes |
| :--- | :--- | :--- | :--- |
| **FastAPI Backend** | `http://10.100.0.1:8000` | `8000` | HTTP / REST API (`/api/v1`) |
| **Admin Backoffice** | `http://10.100.0.1:5173` | `5173` | HTTP (Static SPA via Vite) |
| **Mobile POS App** | `https://10.100.0.1:5174` | `5174` | **HTTPS** (`basic-ssl` required for phone camera `getUserMedia`) |

---

## 3. Repository Layout

```
├── server/                     # FastAPI + SQLModel modular monolith backend
│   ├── main.py                 # App factory & router mounting
│   ├── api/v1/
│   │   ├── router.py           # v1 aggregate router
│   │   └── endpoints/          # users.py, products.py, inventory.py
│   ├── core/
│   │   ├── config.py           # Pydantic settings (DATABASE_URL, SECRET_KEY)
│   │   ├── db.py               # SQLModel / SQLAlchemy engine & session factory
│   │   └── dependencies.py     # get_db(), get_async_db()
│   ├── models/                 # SQLModel tables (User, Product, InventoryLedger)
│   ├── schemas/                # Request & response validation schemas
│   ├── services/               # Business logic & double-entry inventory ledger
│   └── utils/
│       └── barcode.py          # GS1 in-store EAN-13 scale embedded-weight parser
├── apps/                       # Frontend applications (pnpm workspace)
│   ├── pos/                    # Mobile-first Cashier SPA (camera barcode reader, cart, checkout)
│   │   ├── src/lib/camera/     # CameraScanner (@zxing/browser + native BarcodeDetector)
│   │   ├── src/lib/cart/       # Cart state machine in Svelte 5 Runes ($state)
│   │   ├── src/lib/checkout/   # Cash with change calc, Card, QR Mercado Pago
│   │   └── src/lib/audio/      # Web Audio API scanner beeps & error tones
│   └── admin/                  # Backoffice & Operations SPA (responsive phone + desktop)
│       ├── src/routes/         # Catalog with virtual table & product editor
│       ├── src/routes/actions/ # Stock receiving, merma logging, manual adjustments
│       └── src/routes/ledger/  # Double-entry inventory audit ledger with filters
├── packages/                   # Shared monorepo packages
│   ├── api/                    # Centralized @hey-api client, Zod schemas, TanStack Query options
│   ├── ui/                     # Shared Tailwind CSS tokens (@source enabled) & Bits UI primitives
│   └── core/                   # EAN-13 parser, whole ARS currency & weight formatters
├── tests/                      # Pytest suite with isolated SQLite database fixtures
├── Makefile                    # Unified build & test targets (with .devenv in PATH)
├── devenv.nix                  # Nix hermetic environment definition
└── SPECIFICATION.md            # Deep system architecture and domain rules
```

---

## 4. Environment & Execution Cheat Sheet

All tools are provisioned via `devenv.nix` in `.devenv/profile/bin/` and forwarded through `Makefile`:

```bash
make db          # Start PostgreSQL (docker compose up -d postgres)
make dev         # Run FastAPI backend with hot reload (host 0.0.0.0:8000)
make dev-admin   # Run Admin SPA (host 0.0.0.0:5173)
make dev-pos     # Run Mobile POS SPA (host 0.0.0.0:5174, HTTPS)
make lint        # Run ruff check . && biome check .
make fix         # Fix lint errors & auto-format (ruff + biome)
make format      # Auto-format (ruff format . && biome format)
make typecheck   # Fast type-check with ty
make test        # Run pytest test suite
make check       # Full validation: lint, format, ty, pytest, svelte-check & vitest
make build       # Build all frontend SPAs (admin & pos)
make openapi     # Export backend schema to scripts/openapi.json
make codegen     # Export OpenAPI schema and regenerate @vitalcer/api client
```

---

## 5. Current State & Implementation Progress

### Completed Components

1. **Database & Models (Phase 1)**:
   - Migrated to **SQLModel** (`Product`, `User`, `InventoryLedger`).
   - Prices stored as **integers in whole Argentine Pesos (ARS)** (e.g. $1,500 ARS = `1500`). Cents/centavos are strictly omitted.
   - Dual database testing harness (PostgreSQL in production, SQLite in-memory in tests).

2. **Double-Entry Inventory Engine (Phase 3 Backend)**:
   - Append-only ledger movements (`quantity_delta`, `movement_type`, `balance_after`). Direct stock overwrites are forbidden.
   - Transactional endpoints in `/api/v1/inventory`:
     - `/receive` (Inbound supplier stock replenishments)
     - `/merma` (Shrinkage write-offs: spillage, moisture loss, expiration)
     - `/adjust` (Manual inventory reconciliation to physical audit counts)
     - `/reserve` & `/release` (Virtual stock holds for delivery orders)
     - `/fulfill` (Decrements reserved and current stock on dispatch)
     - `/sale-pos` (Physical priority POS cashier sales)
     - `/audit/{product_id}` (Drift detection against full ledger history)
     - `/ledger` (Filtered audit history query)

3. **Admin Operations SPA (`apps/admin`)**:
   - Product catalog with 60 FPS `@tanstack/svelte-virtual` table and search.
   - Responsive product creation/editing modal: transforms into a mobile bottom sheet on phones with internal scrolling, backdrop overlay, and desktop centering.
   - Stock operations dashboard (`/actions`): Inbound receiving, merma logging, and stock adjustments with live product search.
   - Full ledger audit log (`/ledger`) with movement type filters and pagination.

4. **Mobile POS Application (`apps/pos`) (Phase 2)**:
   - Phone-first responsive layout with HTTPS enabled on port `5174` for secure camera access.
   - Camera barcode scanner (`CameraScanner.svelte`) with dual engine: native GPU `BarcodeDetector` + `@zxing/browser` fallback, race-condition guards, torch controls, and camera switching.
   - Cart state machine in Svelte 5 Runes supporting discrete units and weighted bulk grams in whole ARS.
   - Fast in-memory catalog preloading via TanStack Query for 0ms scanner response.
   - Web Audio synthesizer beeps (success scan) and buzzer tones (errors).
   - Checkout modal supporting Cash (quick denominations & change computation), Card terminal, and QR Mercado Pago, committing atomic POS sales to the backend.

### Pending Roadmap Components

1. **Phase 4: Multi-Platform Delivery Orchestration & Live Picking**:
   - `DeliveryOrder` and `DeliveryOrderItem` SQLModel tables.
   - Unified `DeliveryAdapter` interface and mock adapter for local testing.
   - Virtual stock synchronization ($\text{Virtual Stock} = \max(0, \text{Stock} - \text{Reserved} - \text{Buffer})$).
   - Admin live picking screen (`apps/admin/src/routes/deliveries`): acoustic dispatch alerts, picking checklist, and one-click product replacement (*Reemplazo*) with subtotal recalculation.

2. **Phase 5: Financial Closing & Cierre de Caja**:
   - Daily closing service (`/analytics/cierre` or `/reports/cierre`): breakdown across Cash, Cards, and Delivery platform receivables.
   - Admin Cierre de Caja UI (`apps/admin/src/routes/closure`): physical cash count form (*Arqueo de Caja*), discrepancy calculations, and daily shrinkage reports.
