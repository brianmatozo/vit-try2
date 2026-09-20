export PATH := $(CURDIR)/.devenv/profile/bin:$(PATH)

.PHONY: dev dev-pos db lint format fix test check typecheck openapi

db:
	docker compose up -d postgres

dev:
	uv run uvicorn server.main:app --reload

dev-pos:
	pnpm --filter pos dev

lint:
	ruff check .

fix:
	ruff check . --fix && ruff format .

format:
	ruff format .

typecheck:
	ty check

test:
	uv run pytest

check:
	ruff check .
	ruff format --check .
	ty check
	uv run pytest

openapi:
	uv run python scripts/api_export.py
