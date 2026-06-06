# 13 — DevOps, Monorepo, and Deployment

## Local-first deployment

Default deployment is Docker Compose with two services:

- `api` — FastAPI/Python backend;
- `web` — Next.js frontend.

DuckDB is a file mounted into the API container.

```text
./data/raceweek.duckdb
```

## Environment files

Create:

```text
.env.example
.env.local       # user-created, gitignored
```

Never commit `.env.local`.

## Make targets

Required `Makefile` targets:

```makefile
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
```

## Docker Compose

Use the example in `examples/docker-compose.yml` as the starting point.

Requirements:

- API binds to `127.0.0.1:8000` by default.
- Web binds to `127.0.0.1:3000` by default.
- Mount `./data` to persist DuckDB.
- Mount `.env.local` or pass environment variables.
- Do not bake secrets into images.

## Configuration

Use Pydantic Settings in API.

Required settings:

```text
APP_ENV
APP_AUTH_MODE
APP_CORS_ORIGINS
DUCKDB_PATH
FANTASY_API_BASE_URL
FANTASY_GAME_VERSION
OPENF1_BASE_URL
JOLPICA_BASE_URL
OLLAMA_BASE_URL
OPENAI_API_KEY
ANTHROPIC_API_KEY
GOOGLE_API_KEY
OPENROUTER_API_KEY
GROQ_API_KEY
XAI_API_KEY
MISTRAL_API_KEY
CUSTOM_OPENAI_BASE_URL
CUSTOM_OPENAI_API_KEY
```

## Generated contracts

The OpenAPI file is canonical for API clients. Generate TypeScript types during setup:

```bash
pnpm --filter web generate:api-types
```

Suggested tool can be added by implementer, but must be pinned and documented.

## Database initialization

API startup must:

1. ensure data directory exists;
2. open DuckDB;
3. apply migrations;
4. seed provider defaults;
5. seed ruleset defaults;
6. optionally seed license-safe fixtures only for local test/backtest workflows.

Do not seed real current data into the repository.

## Hosted mode

Hosted mode is optional in v1, but architecture must not block it.

Hosted differences:

- require authentication;
- use HTTPS;
- consider Postgres for user data;
- isolate user data;
- encrypt secrets;
- add rate limiting;
- add terms/privacy pages;
- legal review required before public SaaS.

## Release process

Use semantic versioning:

```text
v1.0.0
v1.0.1
v1.1.0
```

Release checklist:

- changelog updated;
- tests pass;
- real-data empty state and source-data onboarding verified;
- docs version updated;
- dependency audit reviewed;
- Docker images build;
- no secrets;
- no official assets;
- GitHub release notes include disclaimer.

## Observability

Local-first observability:

- structured logs;
- request IDs;
- data-source status page;
- connector run logs;
- recommendation run provenance;
- AI provider latency/token metadata where returned;
- no telemetry by default.

Log levels:

- `INFO`: sync started/completed, optimizer run completed.
- `WARNING`: stale data, partial sync, provider fallback.
- `ERROR`: connector failed, database migration failed.

Never log:

- API keys;
- bearer tokens;
- cookies;
- raw provider prompts containing sensitive data;
- user passwords.

## Backup/export

Settings should expose:

- export database snapshot;
- export recommendations as JSON;
- export recommendations as CSV;
- export settings without secrets;
- clear/delete all data.
