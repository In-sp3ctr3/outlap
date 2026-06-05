setup:
	pnpm install --frozen-lockfile
	cd apps/api && uv sync --locked

dev:
	docker compose up --build

api-dev:
	cd apps/api && uv run uvicorn raceweek.api.main:app --reload --host 127.0.0.1 --port 8000

web-dev:
	cd apps/web && pnpm dev

test:
	cd apps/api && uv run pytest
	cd apps/web && pnpm test

lint:
	cd apps/api && uv run ruff check .
	cd apps/api && uv run ruff format --check .
	cd apps/web && pnpm lint

typecheck:
	cd apps/api && uv run mypy src
	cd apps/web && pnpm typecheck

e2e:
	cd apps/web && pnpm e2e

check: lint typecheck test e2e

demo:
	cd apps/api && uv run raceweek seed-demo
	docker compose up --build
