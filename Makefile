# Convenience commands for Unix-like shells (macOS/Linux/WSL).
# Windows/PowerShell users: see README.md "Local setup (Windows)" for the
# equivalent commands -- `make` is not assumed to be installed on Windows.

.PHONY: api-install api-migrate api-seed api-dev api-test web-install web-dev web-build web-test test up down

api-install:
	cd apps/api && python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"

api-migrate:
	cd apps/api && . .venv/bin/activate && alembic upgrade head

api-seed:
	cd apps/api && . .venv/bin/activate && python -c "from app.db.session import SessionLocal; from app.knowledge.seed import seed_all; db = SessionLocal(); print(seed_all(db)); db.close()"

api-dev:
	cd apps/api && . .venv/bin/activate && uvicorn app.main:app --reload --port 8000

api-test:
	cd apps/api && . .venv/bin/activate && pytest -q

web-install:
	cd apps/web && npm install

web-dev:
	cd apps/web && npm run dev

web-build:
	cd apps/web && npm run build

web-test:
	cd apps/web && npm test

test: api-test web-test

up:
	docker compose up --build

down:
	docker compose down
