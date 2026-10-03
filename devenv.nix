{ pkgs, lib, config, inputs, ... }:

{
  # Environment variables
  env = {
    # Let uv manage standalone Python 3.14 toolchains hermetically
    UV_PYTHON_PREFERENCE = "managed";
    # Default database URL for local development (matches docker-compose & postgres service)
    DATABASE_URL = "postgresql://vitalcer:vitalcer@localhost:5432/vitalcer";
    PGDATABASE = "vitalcer";
    PGUSER = "vitalcer";
  };

  # CLI tools and language servers
  packages = with pkgs; [
    # Astral Python toolchain (Rust-based, zero Node.js dependencies)
    uv               # Fast Python package & project manager
    ruff             # Extremely fast linter and formatter
    ty               # Astral's lightning-fast type checker & LSP (in Rust)

    # Mature type checking & LSP
    basedpyright     # Comprehensive type checker and language server

    # Svelte & Frontend Toolchain
    nodejs_22        # Required runtime for pnpm, Vite, and Svelte tooling
    pnpm             # Monorepo workspace package manager
    biome            # Ultra-fast Rust-based JS/TS linter & formatter (replaces ESLint + Prettier)

    # Frontend Language Servers
    # Note: There is currently NO non-Node alternative for Svelte LSP.
    # Svelte 5 runes ($state, $derived) and component typecheck require the official svelte-language-server.
    svelte-language-server
    vtsls            # Fast, high-performance TypeScript language server (for pure .ts files)
    typescript       # tsc compiler for typecheck scripts
    tailwindcss-language-server # Optional Tailwind CSS class completion

    # System & Database utilities
    postgresql_18    # psql CLI, pg_dump, and postgres tools matching docker-compose
    pkg-config
    harlequin        # Terminal SQL IDE / DB viewer
    marksman         # Markdown LSP
    # lua-language-server
    # stylua
  ];

  # Devenv helper commands (run directly in shell or with `devenv run <name>`)
  scripts = {
    dev.exec = "uv run uvicorn server.main:app --reload --host 0.0.0.0";
    lint.exec = "ruff check .";
    fix.exec = "ruff check . --fix && ruff format .";
    format.exec = "ruff format .";
    "typecheck:fast".exec = "ty check";
    typecheck.exec = "basedpyright";
    test.exec = "uv run pytest";
    check.exec = ''
      echo "==> Linting with ruff..."
      ruff check .
      echo "==> Checking format with ruff..."
      ruff format --check .
      echo "==> Type-checking with ty..."
      ty check
      echo "==> Running tests with pytest..."
      uv run pytest
    '';
    openapi.exec = "uv run python scripts/api_export.py";

    # Frontend scripts
    "dev:admin".exec = "pnpm --filter admin dev -- --host";
    "dev:pos".exec = "pnpm --filter pos dev -- --host";
    "check:admin".exec = "pnpm --filter admin check";
    "check:pos".exec = "pnpm --filter pos check";
    "lint:fe".exec = "biome check .";
    "format:fe".exec = "biome format --write .";
  };

  # Background processes managed by `devenv up`
  processes = {
    server.exec = ''
      echo "Waiting for PostgreSQL to be ready on port 5432..."
      while ! pg_isready -h 127.0.0.1 -p 5432 -d vitalcer -U vitalcer -q; do
        sleep 0.5
      done
      echo "PostgreSQL is ready, starting backend server..."
      uv run uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
    '';
  };

  # Native PostgreSQL service managed by devenv
  services.postgres = {
    enable = true;
    package = pkgs.postgresql_18;
    listen_addresses = "127.0.0.1";
    port = 5432;
    initialDatabases = [
      { name = "vitalcer"; user = "vitalcer"; }
      { name = "brian"; user = "vitalcer"; }
    ];
    initialScript = ''
      DO $$
      BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'vitalcer') THEN
          CREATE USER vitalcer WITH PASSWORD 'vitalcer' SUPERUSER;
        ELSE
          ALTER USER vitalcer WITH PASSWORD 'vitalcer' SUPERUSER;
        END IF;
      END
      $$;
    '';
  };

  # Shell setup hook
  enterShell = ''
    # Auto-initialize local virtual environment with uv if not present
    if [ ! -d ".venv" ]; then
      echo "Initializing virtual environment with uv..."
      uv sync
    fi

    echo ""
    echo "  Vitalcer dev environment loaded"
    echo "  Backend (Python):"
    echo "    • uv:            $(uv --version 2>/dev/null || echo 'available')"
    echo "    • ruff:          $(ruff --version 2>/dev/null || echo 'available')"
    echo "    • ty (fast LSP): $(ty --version 2>/dev/null || echo 'available')"
    echo "    • basedpyright:  $(basedpyright --version 2>/dev/null | head -n1 || echo 'available')"
    echo "  Frontend (Svelte):"
    echo "    • pnpm:          $(pnpm --version 2>/dev/null || echo 'available')"
    echo "    • biome (Rust):  $(biome --version 2>/dev/null || echo 'available')"
    echo "    • svelte-lsp:    $(svelteserver --version 2>/dev/null || echo 'available')"
    echo "    • vtsls (TS LSP):$(vtsls --version 2>/dev/null || echo 'available')"
    echo ""
    echo "Commands: dev, dev:pos, check, check:pos, lint, lint:fe, format, format:fe, test"
  '';
}

