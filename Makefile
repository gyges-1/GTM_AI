.PHONY: install install-fe docker-up docker-down migrate dev dev-fe test test-unit test-agent lint format typecheck clean

PYTHON := .venv/bin/python
UV     := python3 -m uv

# ── Python ────────────────────────────────────────────────────────────────────
install:
	$(UV) venv .venv --python python3.13
	$(UV) pip install -e ".[dev]" --python .venv/bin/python

# ── Frontend ──────────────────────────────────────────────────────────────────
install-fe:
	cd frontend && npm install

# ── Docker ────────────────────────────────────────────────────────────────────
docker-up:
	docker compose up -d postgres langfuse
	@echo "Waiting for Postgres to be ready..."
	@sleep 3

docker-down:
	docker compose down

# ── Database ──────────────────────────────────────────────────────────────────
migrate:
	.venv/bin/alembic upgrade head

migrate-create:
	.venv/bin/alembic revision --autogenerate -m "$(MSG)"

# ── Dev servers ───────────────────────────────────────────────────────────────
dev:
	.venv/bin/uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

dev-fe:
	cd frontend && npm run dev

# ── Testing ───────────────────────────────────────────────────────────────────
test:
	.venv/bin/pytest tests/ -v

test-unit:
	.venv/bin/pytest tests/unit -v

test-integration:
	.venv/bin/pytest tests/integration -v

test-agent:
	$(PYTHON) scripts/test_agent.py

# ── Code quality ─────────────────────────────────────────────────────────────
lint:
	.venv/bin/ruff check backend/ tests/

format:
	.venv/bin/ruff format backend/ tests/

typecheck:
	.venv/bin/mypy backend/

# ── Utilities ─────────────────────────────────────────────────────────────────
seed:
	$(PYTHON) scripts/seed_db.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache
