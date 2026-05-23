.PHONY: dev lint format fix test check openapi

dev:
	uv run uvicorn app.main:app --reload

lint:
	uv run ruff check .

fix:
	uv run ruff check . --fix

format:
	uv run ruff format .

test:
	uv run pytest

check:
	uv run ruff check .
	uv run pytest

openapi:
	uv run python scripts/api_export.py
