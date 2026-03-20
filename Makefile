.PHONY: help up down logs test lint format install check-env nemoclaw-install

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies with uv
	uv sync

nemoclaw-install: ## Install NVIDIA NeMo-Claw on the host
	@echo "Installing NVIDIA NeMo-Claw..."
	curl -fsSL https://nvidia.com/nemoclaw.sh | bash
	@echo "Run: nemoclaw onboard — to configure the agent"

check-env:
	@test -f .env || { echo "ERROR: Run: cp .env.example .env"; exit 1; }
	@test -f config.yaml || { echo "ERROR: Run: cp config.yaml.example config.yaml"; exit 1; }
	@echo "✅ Environment files OK"

up: check-env ## Start the full stack
	docker compose up -d
	@echo "API: http://localhost:$${API_PORT:-8080}"

up-infra: check-env ## Start infrastructure only
	docker compose up -d postgres milvus-standalone etcd otel-collector

down:
	docker compose down

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

dev: check-env
	uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port $${API_PORT:-8080}

test:
	uv run pytest tests/ -v

test-unit:
	uv run pytest tests/unit/ -v

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

typecheck:
	uv run mypy src/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true

nemoclaw-status: ## Check NeMo-Claw status
	nemoclaw status 2>/dev/null || echo "NeMo-Claw not installed. Run: make nemoclaw-install"
