# 03 — Tech Stack and Version Pins

Version pins reflect a June 5, 2026 implementation baseline. The implementation agent must create lockfiles and avoid floating versions.

## Architecture summary

- **Monorepo:** pnpm workspace.
- **Frontend:** Next.js + React + TypeScript + Tailwind + shadcn-style components.
- **Backend:** FastAPI + Pydantic + Python.
- **Analytics store:** DuckDB local file.
- **Data processing:** Polars + pandas/FastF1 where needed.
- **Optimization:** OR-Tools CP-SAT with brute-force fallback for small candidate sets.
- **AI providers:** self-authored adapter layer using official SDKs or OpenAI-compatible clients.
- **Testing:** pytest, Vitest, Playwright.
- **Deployment:** Docker Compose local-first.

## Runtime pins

| Tool | Version | Purpose |
|---|---:|---|
| Python | 3.13.13 | Backend runtime; conservative compatibility baseline |
| Node.js | 24.16.0 | Web runtime; LTS line |
| pnpm | 11.5.2 | JS package manager |
| uv | 0.11.19 | Python package/project manager |
| Docker | 26+ | Local containers; exact engine handled by user environment |
| Docker Compose | v2.38+ | Local orchestration |

## Frontend dependencies

Pin these in `apps/web/package.json`.

```json
{
  "dependencies": {
    "@tanstack/react-query": "5.101.0",
    "lucide-react": "1.17.0",
    "next": "16.2.7",
    "react": "19.2.7",
    "react-dom": "19.2.7",
    "recharts": "3.8.1",
    "zod": "4.4.3"
  },
  "devDependencies": {
    "@playwright/test": "1.60.0",
    "@tailwindcss/postcss": "4.3.0",
    "eslint": "10.4.1",
    "eslint-config-next": "16.2.7",
    "prettier": "3.8.3",
    "tailwindcss": "4.3.0",
    "typescript": "6.0.3",
    "vitest": "4.1.8"
  }
}
```

Notes:

- Use React Server Components for static layout and client components for interactive widgets.
- Use TanStack Query for API data fetching/caching.
- Use Zod for runtime validation at the frontend boundary.
- Use Recharts for simple dashboard charts. Do not build a custom charting engine in v1.
- Use shadcn-style generated components; do not make `shadcn` a runtime dependency.

## Backend dependencies

Pin these in `apps/api/pyproject.toml`.

```toml
[project]
requires-python = "==3.13.*"
dependencies = [
  "fastapi==0.136.3",
  "uvicorn==0.49.0",
  "pydantic==2.13.4",
  "pydantic-settings==2.14.1",
  "httpx==0.28.1",
  "orjson==3.11.9",
  "duckdb==1.5.3",
  "polars==1.41.2",
  "pandas==3.0.3",
  "fastf1==3.8.3",
  "feedparser==6.0.12",
  "ortools==9.15.6755",
  "scikit-learn==1.9.0",
  "scipy==1.16.3",
  "apscheduler==3.11.2",
  "croniter==6.2.2",
  "tenacity==9.1.4",
  "python-dotenv==1.2.2",
  "openai==2.41.0",
  "anthropic==0.105.2",
  "ollama==0.6.2",
  "google-genai==2.8.0",
  "mistralai==2.4.9"
]

[dependency-groups]
dev = [
  "pytest==9.0.3",
  "pytest-cov==7.1.0",
  "respx==0.23.1",
  "ruff==0.15.16",
  "mypy==2.1.0"
]
```

Security note: do not add LiteLLM as a core runtime dependency in v1. Implement a small provider adapter layer. If a maintainer later wants LiteLLM, make it an optional gateway integration and pin to a known-safe deployment path.

## Why this stack

### Next.js + FastAPI instead of a single full-stack framework

The web UI and analytics engine have different needs. Next.js is excellent for a polished dashboard. FastAPI/Python is a better fit for connectors, optimization, projections, data science libraries, and provider SDKs.

### DuckDB instead of Postgres for default mode

The open-source default should be local-first, zero-admin, and portable. DuckDB provides a single-file analytical database, strong SQL support, and simple exports. Hosted mode can add Postgres later without changing domain contracts.

### OR-Tools plus brute-force fallback

The fantasy lineup search space is small enough to brute-force in many cases, but chip/transfer constraints benefit from a solver. Implement both:

- brute-force for simple reproducibility and debugging;
- OR-Tools for more complex constraints and future plugins.

### Self-authored provider adapters

AI provider APIs change, and all-in-one routing libraries increase supply-chain and abstraction risk. The v1 provider layer should be small, typed, and easy to audit.

## Package hygiene

- Commit lockfiles: `pnpm-lock.yaml` and `uv.lock`.
- Do not use `latest` or caret ranges in production dependencies.
- Enable Dependabot/Renovate, but require tests and changelog review.
- Pin GitHub Actions by SHA in CI.
- Use secret scanning and dependency audit in CI.
- Never install package versions known to be compromised.

## Development commands

```bash
make setup       # install web/backend dependencies
make dev         # run web + API locally
make test        # all tests
make lint        # ruff + eslint
make typecheck   # mypy + tsc
make e2e         # Playwright
make check       # lint + typecheck + tests
make demo        # load fixture data and run app
```
