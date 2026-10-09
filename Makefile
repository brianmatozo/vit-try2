DEVENV_BIN := $(CURDIR)/.devenv/profile/bin
export PATH := $(DEVENV_BIN):$(PATH)

.PHONY: up dev dev-admin dev-pos db lint format fix test check typecheck openapi codegen codegen-watch build build-admin build-pos serve caddy-validate caddy-reload

up:
	@devenv up

db:
	@$(DEVENV_BIN)/db

dev:
	@$(DEVENV_BIN)/dev

dev-admin: codegen
	@$(DEVENV_BIN)/dev-admin

dev-pos: codegen
	@$(DEVENV_BIN)/dev-pos

lint:
	@$(DEVENV_BIN)/lint

fix:
	@$(DEVENV_BIN)/fix

format:
	@$(DEVENV_BIN)/format

typecheck:
	@$(DEVENV_BIN)/typecheck

test:
	@$(DEVENV_BIN)/test

check: codegen
	@$(DEVENV_BIN)/check

openapi:
	@$(DEVENV_BIN)/openapi

codegen:
	@$(DEVENV_BIN)/codegen

codegen-watch:
	@$(DEVENV_BIN)/codegen-watch

build: codegen
	@$(DEVENV_BIN)/build

build-admin: codegen
	@$(DEVENV_BIN)/build-admin

build-pos: codegen
	@$(DEVENV_BIN)/build-pos

serve: build
	@$(DEVENV_BIN)/serve

caddy-validate:
	@$(DEVENV_BIN)/caddy:validate

caddy-reload:
	@$(DEVENV_BIN)/serve:reload


