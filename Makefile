# totem-checkout — developer workflow
# All commands run from the repo root; backend targets cd into backend/.

BACKEND := backend
UV := uv

.PHONY: help install lint format check test openapi up down reset build run

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

install: ## Install backend dependencies (uv sync)
	cd $(BACKEND) && $(UV) sync

lint: ## Lint with ruff
	cd $(BACKEND) && $(UV) run ruff check .

format: ## Auto-format with ruff
	cd $(BACKEND) && $(UV) run ruff format .

check: ## Quality gate: lint + format check + tests
	cd $(BACKEND) && $(UV) run ruff check . && $(UV) run ruff format --check . && $(UV) run pytest -q

test: ## Run the test suite
	cd $(BACKEND) && $(UV) run pytest

openapi: ## Regenerate the committed OpenAPI spec (openapi.json)
	cd $(BACKEND) && $(UV) run python scripts/generate_openapi.py

build: ## Build the backend docker image
	cd $(BACKEND) && docker compose build

up: ## Bring the full stack online (db + migrations + backend + frontend)
	cd $(BACKEND) && docker compose up -d --build

down: ## Stop the stack (keeps the database volume)
	cd $(BACKEND) && docker compose down

reset: ## Stop the stack and wipe the database volume (irreversible)
	cd $(BACKEND) && docker compose down -v

run: ## Run the dev server locally (needs a reachable DATABASE_URL)
	cd $(BACKEND) && $(UV) run python -m src.main
