# Vitalcer Monorepo — Project Context

> **Note for AI Agents**: For immediate developer environment instructions and toolchain execution, see [AGENTS.md](AGENTS.md). For deep technical specifications and domain rules, see [SPECIFICATION.md](SPECIFICATION.md).

---

## 1. Overview

**Vitalcer** is a single-store dietetic store management system (*dietética*) handling both **discrete unit goods** and **continuous bulk goods** (grams, embedded-weight EAN-13 scale barcodes) alongside multi-platform delivery fulfillment (**PedidosYa, Rappi, VGO, MercadoLibre**).

- **Architecture**: Modular Monolith backend paired with decoupled static SvelteKit SPAs.
- **Backend**: Python >= 3.14, FastAPI, SQLModel, FastCRUD (`server/`).
- **Frontend**: Svelte 5, SvelteKit static SPAs (`apps/pos`, `apps/admin`), TanStack Suite (`Query`, `Table`, `Form`, `Virtual`), Tailwind CSS v4, Bits UI / shadcn-svelte (`apps/*`, `packages/*`).
- **Toolchain**: Nix `devenv.nix` (`uv`, `ruff`, `ty`, `basedpyright`, `pnpm`, `postgresql_18`).
- **Database**: PostgreSQL 18 (production/docker) / SQLite (isolated in tests).

---

## 2. Repository Layout

```
├── server/                     # FastAPI + SQLModel backend
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
│   ├── pos/                    # Cashier counter SPA (SvelteKit static)
│   └── admin/                  # Backoffice & deliveries SPA (SvelteKit static)
├── packages/                   # Shared monorepo packages
│   ├── api/                    # Auto-generated @hey-api client, Zod schemas, TanStack Query options
│   ├── ui/                     # Shared Tailwind CSS tokens & Bits UI / shadcn-svelte primitives
│   └── core/                   # Shared EAN-13 parser, ARS currency & weight formatters
├── tests/                      # Pytest suite with isolated SQLite database fixtures
├── Makefile                    # Pre-configured build & test targets (with .devenv in PATH)
├── devenv.nix                  # Nix environment definition
└── SPECIFICATION.md            # System architecture and technical specifications
```

---

## 3. Environment & Execution Cheat Sheet

All tools are provisioned via `devenv.nix` in `.devenv/profile/bin/`:

```bash
make dev         # Run FastAPI backend with hot reload
make lint        # Run ruff check .
make fix         # Fix lint errors & auto-format with ruff
make format      # Format with ruff
make typecheck   # Fast typecheck with ty
make test        # Run pytest test suite
make check       # Full validation: lint + format check + typecheck + pytest
make openapi     # Export backend schema to scripts/openapi.json
```

---

## 4. Current State & Implementation Progress

1. **Database & Models**: Migrated to **SQLModel** (`Product`, `User`, `InventoryLedger`).
2. **Pricing Convention**: Stored as **integers in whole Argentine Pesos (ARS)**. Cents/centavos are strictly omitted.
3. **Inventory Ledger**: Double-entry append-only ledger (`quantity_delta`, `movement_type`, `balance_after`). Direct stock overwrites are forbidden.
4. **Barcode Engine**: EAN-13 embedded-weight scale barcode parser implemented and tested (`server/utils/barcode.py`).
5. **Frontend Setup**: `apps/pos` and `apps/admin` defined as separated static SvelteKit SPAs using the TanStack suite and Tailwind CSS.
