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
    caddy            # Fast HTTP/2 & HTTP/3 web server with automatic TLS & Brotli
    pkg-config
    harlequin        # Terminal SQL IDE / DB viewer
    marksman         # Markdown LSP
    # lua-language-server
    # stylua
  ];

  # Devenv helper commands (run directly in shell or with `devenv run <name>`)
  scripts = {
    # Backend Development
    dev.exec = "uv run uvicorn server.main:app --reload --host 0.0.0.0";
    "dev:be".exec = "uv run uvicorn server.main:app --reload --host 0.0.0.0";
    db.exec = "docker compose up -d postgres";

    # Frontend Development (supports both hyphen and colon syntax)
    "dev-admin".exec = "pnpm --filter admin dev";
    "dev:admin".exec = "pnpm --filter admin dev";
    "dev-pos".exec = "pnpm --filter pos dev";
    "dev:pos".exec = "pnpm --filter pos dev";

    # Production Builds
    build.exec = "uv run python scripts/api_export.py && pnpm --filter @vitalcer/api generate && pnpm -r --filter './apps/*' build && node scripts/compress_static.mjs";
    "build:all".exec = "uv run python scripts/api_export.py && pnpm --filter @vitalcer/api generate && pnpm -r --filter './apps/*' build && node scripts/compress_static.mjs";
    "build-admin".exec = "uv run python scripts/api_export.py && pnpm --filter @vitalcer/api generate && pnpm --filter admin build && node scripts/compress_static.mjs";
    "build:admin".exec = "uv run python scripts/api_export.py && pnpm --filter @vitalcer/api generate && pnpm --filter admin build && node scripts/compress_static.mjs";
    "build-pos".exec = "uv run python scripts/api_export.py && pnpm --filter @vitalcer/api generate && pnpm --filter pos build && node scripts/compress_static.mjs";
    "build:pos".exec = "uv run python scripts/api_export.py && pnpm --filter @vitalcer/api generate && pnpm --filter pos build && node scripts/compress_static.mjs";

    # Linting & Formatting (Unified & Granular)
    lint.exec = "echo '==> Ruff linting...' && ruff check . && echo '==> Biome linting...' && biome check .";
    "lint:be".exec = "ruff check .";
    "lint:fe".exec = "biome check .";
    format.exec = "ruff format . && biome format --write .";
    "format:be".exec = "ruff format .";
    "format:fe".exec = "biome format --write .";
    fix.exec = "ruff check . --fix && ruff format . && biome check --write .";
    "fix:be".exec = "ruff check . --fix && ruff format .";
    "fix:fe".exec = "biome check --write .";

    # Type Checking
    typecheck.exec = "ty check";
    "typecheck:fast".exec = "ty check";
    "typecheck:strict".exec = "basedpyright";
    "typecheck:fe".exec = "uv run python scripts/api_export.py && pnpm --filter @vitalcer/api generate && pnpm --filter admin check && pnpm --filter pos check";

    # Testing
    test.exec = "uv run pytest";
    "test:be".exec = "uv run pytest";
    "test:fe".exec = "pnpm --filter core test";
    "test:all".exec = "uv run pytest && pnpm --filter core test";

    # Full Verification Pipeline
    check.exec = ''
      echo "=========================================="
      echo "==> [Backend] Linting with ruff..."
      ruff check .
      echo "==> [Backend] Checking format with ruff..."
      ruff format --check .
      echo "==> [Backend] Type-checking with ty..."
      ty check
      echo "==> [Backend] Running pytest test suite..."
      uv run pytest
      echo "==> [API] Regenerating client for frontend validation..."
      uv run python scripts/api_export.py && pnpm --filter @vitalcer/api generate
      echo "==> [Frontend] Linting with biome..."
      biome check .
      echo "==> [Frontend] Checking admin app (svelte-check)..."
      pnpm --filter admin check
      echo "==> [Frontend] Checking pos app (svelte-check)..."
      pnpm --filter pos check
      echo "==> [Frontend] Running core package tests..."
      pnpm --filter core test
      echo "=========================================="
      echo "All monorepo checks passed successfully!"
      echo "=========================================="
    '';
    "check:be".exec = ''
      echo "==> [Backend] Linting with ruff..."
      ruff check .
      echo "==> [Backend] Checking format with ruff..."
      ruff format --check .
      echo "==> [Backend] Type-checking with ty..."
      ty check
      echo "==> [Backend] Running pytest test suite..."
      uv run pytest
    '';
    "check:fe".exec = ''
      echo "==> [API] Regenerating client for frontend validation..."
      uv run python scripts/api_export.py && pnpm --filter @vitalcer/api generate
      echo "==> [Frontend] Linting with biome..."
      biome check .
      echo "==> [Frontend] Checking admin app (svelte-check)..."
      pnpm --filter admin check
      echo "==> [Frontend] Checking pos app (svelte-check)..."
      pnpm --filter pos check
      echo "==> [Frontend] Running core package tests..."
      pnpm --filter core test
    '';
    "check-admin".exec = "uv run python scripts/api_export.py && pnpm --filter @vitalcer/api generate && pnpm --filter admin check";
    "check:admin".exec = "uv run python scripts/api_export.py && pnpm --filter @vitalcer/api generate && pnpm --filter admin check";
    "check-pos".exec = "uv run python scripts/api_export.py && pnpm --filter @vitalcer/api generate && pnpm --filter pos check";
    "check:pos".exec = "uv run python scripts/api_export.py && pnpm --filter @vitalcer/api generate && pnpm --filter pos check";

    # OpenAPI & API Client Codegen
    openapi.exec = "uv run python scripts/api_export.py";
    codegen.exec = "uv run python scripts/api_export.py && pnpm --filter @vitalcer/api generate";
    "api:generate".exec = "uv run python scripts/api_export.py && pnpm --filter @vitalcer/api generate";
    "codegen-watch".exec = "uv run watchfiles --filter python 'uv run python scripts/api_export.py && pnpm --filter @vitalcer/api generate' server/";
    "codegen:watch".exec = "uv run watchfiles --filter python 'uv run python scripts/api_export.py && pnpm --filter @vitalcer/api generate' server/";

    # Caddy Static Server & High-Speed Asset Serving
    serve.exec = "caddy run --config Caddyfile";
    "serve:reload".exec = "caddy reload --config Caddyfile";
    "caddy:validate".exec = "caddy validate --config Caddyfile";
  };

  # Background processes managed by `devenv up`
  processes = {
    server.exec = ''
      echo "Waiting for PostgreSQL to be ready on port 5432..."
      while ! pg_isready -h 127.0.0.1 -p 5432 -d vitalcer -U vitalcer -q; do
        sleep 0.5
      done
      echo "PostgreSQL is ready, starting backend server on 0.0.0.0:8000..."
      uv run uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
    '';
    admin.exec = "pnpm --filter admin dev";
    pos.exec = "pnpm --filter pos dev";
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

    # Auto-generate API client stubs if not present
    if [ ! -d "packages/api/src/generated" ]; then
      echo "Generating API client stubs..."
      uv run python scripts/api_export.py && pnpm --filter @vitalcer/api generate
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
    echo "  Web Server & Proxy:"
    echo "    • caddy:         $(caddy version 2>/dev/null | head -n1 || echo 'available')"
    echo ""
    echo "  Commands available:"
    echo "    • Dev:       dev, dev-admin (dev:admin), dev-pos (dev:pos), db"
    echo "    • Serve:     serve, serve:reload, caddy:validate"
    echo "    • Check:     check, check:be, check:fe, check-admin, check-pos"
    echo "    • Lint/Fix:  lint, format, fix (or :be / :fe)"
    echo "    • Typecheck: typecheck (ty), typecheck:strict (basedpyright)"
    echo "    • Test:      test (pytest), test:fe, test:all"
    echo "    • Build:     build, build-admin, build-pos"
    echo "    • API:       openapi, codegen (api:generate)"
    echo ""
  '';
}

