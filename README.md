# Vitalcer

Management system for dietetic retail stores (*dietéticas*), supporting discrete unit products and continuous bulk goods (grams, embedded-weight EAN-13 barcodes) alongside multi-channel delivery order fulfillment (**PedidosYa, Rappi, VGO, MercadoLibre**).

## Architecture

- **Backend**: Python 3.14 + FastAPI + SQLModel + FastCRUD (Modular Monolith under `server/`).
- **Frontend**: Svelte 5 + SvelteKit static SPAs (`apps/pos`, `apps/admin`) + TanStack (Query, Table, Form, Virtual) in a pnpm monorepo.
- **Toolchain**: Nix hermetic environment via `devenv.nix` (`uv`, `ruff`, `ty`, `basedpyright`, `pnpm`, `postgresql_18`).

## Quick Start

```bash
# Enter development shell (or run via make directly)
make dev         # Start backend with auto-reload
make check       # Run linter, typecheck, and test suite
make openapi     # Export OpenAPI spec for frontend clients
```

See [AGENTS.md](AGENTS.md) for environment details and [SPECIFICATION.md](SPECIFICATION.md) for system architecture and domain models.
