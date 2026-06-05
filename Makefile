.PHONY: setup dev api web test lint typecheck e2e check demo

setup:
	pnpm install
	cd apps/api && uv sync

dev:
	(cd apps/api && uv run uvicorn raceweek.main:app --reload --host 127.0.0.1 --port 8000) & \
	(cd apps/web && pnpm dev --hostname 127.0.0.1 --port 3000)

api:
	cd apps/api && uv run uvicorn raceweek.main:app --reload --host 127.0.0.1 --port 8000

web:
	cd apps/web && pnpm dev --hostname 127.0.0.1 --port 3000

test:
	cd apps/api && uv run pytest
	pnpm --recursive test

lint:
	cd apps/api && uv run ruff check src tests
	pnpm --recursive lint

typecheck:
	cd apps/api && uv run mypy src
	pnpm --recursive typecheck

e2e:
	pnpm --filter web e2e

check: lint typecheck test e2e

demo:
	cd apps/api && uv run raceweek demo
