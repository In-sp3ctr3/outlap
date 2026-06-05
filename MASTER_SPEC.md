# RaceWeek Strategist v1 — Master Specification

This is a concatenated copy of the multi-file documentation package. Prefer the individual files for implementation.


---

<!-- BEGIN README.md -->

# RaceWeek Strategist v1 Documentation Package

This package is a build-ready specification for an open-source, local-first, bring-your-own-AI fantasy motorsport strategy dashboard.

The project deliberately avoids official Formula 1 branding in its name and UI. The recommended public product name is **RaceWeek Strategist**. The product may describe itself as an unofficial fantasy motorsport analytics tool, but must not imply affiliation, endorsement, sponsorship, or official status.

## How to use this package

Give this entire folder to the implementation agent. The agent should read the files in this order:

1. `AGENTS.md`
2. `docs/00_IMPLEMENTATION_AGENT_BRIEF.md`
3. `docs/01_PRD.md`
4. `docs/02_PRODUCT_SCOPE_FEATURES.md`
5. `docs/03_TECH_STACK_AND_VERSIONS.md`
6. `docs/04_ARCHITECTURE.md`
7. `docs/05_DATA_SOURCES_AND_CONNECTORS.md`
8. `docs/06_DOMAIN_MODEL_DATABASE_SCHEMA.md`
9. `api/openapi.yaml`
10. `schemas/*.json`
11. `docs/08_AI_PROVIDER_AGENT_ARCHITECTURE.md`
12. `docs/09_OPTIMIZER_PROJECTION_ENGINE.md`
13. `docs/10_UI_UX_DESIGN_SYSTEM.md`
14. `docs/11_SECURITY_PRIVACY_LEGAL.md`
15. `docs/12_TESTING_TDD_QA.md`
16. `docs/13_DEVOPS_MONOREPO_DEPLOYMENT.md`
17. `docs/14_IMPLEMENTATION_PLAN.md`
18. `docs/adrs/*.md`

`MASTER_SPEC.md` is a concatenated version of the main documentation for agents that work better with one large file.

## Non-negotiable v1 product stance

- v1 is a polished product, not a throwaway MVP.
- The LLM is not the source of truth. Rules, prices, projections, and recommendations come from deterministic services and stored data snapshots.
- All fantasy transfers remain human-approved. v1 must not auto-submit changes to the official fantasy game.
- Data connectors must be adapter-based and resilient to upstream changes.
- The app is local-first and open-source by default.
- AI provider keys are bring-your-own-key. No telemetry is enabled by default.
- The UI must be polished enough for public open-source launch.

## Repository name suggestion

Recommended repository name: `raceweek-strategist`.

Avoid names that imply official affiliation, such as `official-f1-fantasy-ai`, `f1-official-strategist`, or names using Formula 1 trademarks as branding.


<!-- END README.md -->


---

<!-- BEGIN AGENTS.md -->

# Implementation Agent Instructions

You are implementing RaceWeek Strategist v1.

## Read-before-build checklist

Before writing code, read:

1. `docs/00_IMPLEMENTATION_AGENT_BRIEF.md`
2. `docs/01_PRD.md`
3. `docs/03_TECH_STACK_AND_VERSIONS.md`
4. `docs/04_ARCHITECTURE.md`
5. `docs/05_DATA_SOURCES_AND_CONNECTORS.md`
6. `docs/06_DOMAIN_MODEL_DATABASE_SCHEMA.md`
7. `api/openapi.yaml`
8. `schemas/*.json`
9. `docs/12_TESTING_TDD_QA.md`
10. `docs/adrs/*.md`

## Hard rules

1. Do not invent external API endpoints.
   - Only use external endpoints documented in `docs/05_DATA_SOURCES_AND_CONNECTORS.md`.
   - If an upstream endpoint changes or is unavailable, implement the configured fallback path and surface a data-health warning.

2. Write tests before implementation for core domain behavior.
   - Rules engine, transfer counting, chip simulation, optimizer constraints, and recommendation scoring must be test-first.

3. The LLM must never calculate final scores, budgets, transfer penalties, or optimized lineups.
   - The LLM can explain and compare outputs from deterministic services.
   - The LLM can call read-only tools.
   - The LLM cannot submit transfers or mutate the fantasy account.

4. No official Formula 1 logos, team logos, driver images, broadcast graphics, proprietary timing feeds, or copyrighted media in the repository.

5. User secrets must never appear in logs, snapshots, test fixtures, crash reports, analytics, or generated prompts.

6. All code paths that use live external data must save provenance:
   - source name
   - connector version
   - request path, excluding secrets
   - fetched timestamp
   - response hash
   - normalization version

7. Build local-first first.
   - Hosted/SaaS deployment is optional and must not weaken privacy defaults.

## Definition of done for any feature

A feature is done only when:

- typed contracts exist;
- unit tests exist for domain logic;
- API tests exist for public endpoints;
- UI loading/empty/error states exist;
- data provenance is recorded where external data is involved;
- docs are updated;
- accessibility basics pass;
- secrets are redacted in logs;
- `make check` passes.

## Expected implementation style

- Prefer pure functions in `packages/core` / `apps/api/src/raceweek/core`.
- Keep framework code thin.
- Add adapters at the edges.
- Use dependency injection for data sources and AI providers.
- Make invalid states unrepresentable with Pydantic and TypeScript/Zod contracts.
- Prefer explicit models over dictionaries in domain code.
- Prefer simple deterministic algorithms before machine learning.
- Do not add dependencies without updating `docs/03_TECH_STACK_AND_VERSIONS.md` and lockfiles.


<!-- END AGENTS.md -->


---

<!-- BEGIN docs/00_IMPLEMENTATION_AGENT_BRIEF.md -->

# 00 — Implementation Agent Brief

## Product summary

**RaceWeek Strategist** is an open-source, local-first, AI-assisted fantasy motorsport strategy platform. It helps users make informed fantasy lineup decisions by combining fantasy asset prices and scores, user team state, transfer/chip rules, race results, session data, weather, news, projections, and deterministic optimization.

The product is not merely a dashboard and not merely a chatbot. It is a **strategy system**:

1. ingest data;
2. normalize and snapshot it;
3. calculate features;
4. produce projections;
5. optimize legal transfer/chip scenarios;
6. explain recommendations using a bring-your-own-AI provider.

## v1 quality bar

The user explicitly wants v1 to be polished. Do not interpret v1 as a minimal prototype. v1 includes all features in this specification. Future versions may add new community ideas, but v1 must be complete enough to publish as a serious open-source product.

## Core promise

> Given my fantasy team, budget, transfer allowance, chip state, race-week context, prices, projections, and risk appetite, recommend the best moves and explain the tradeoffs.

## Required v1 capabilities

- Local-first setup with Docker Compose.
- Polished responsive web UI.
- Current fantasy team import by manual JSON/CSV and optional authenticated connector.
- Fantasy asset market with price, score, ownership, value, recent form, risk, and projected movement fields.
- Race-week dashboard with sessions, results, race-control flags, weather, and news.
- Deterministic projection engine.
- Deterministic optimizer for legal lineups, transfers, chips, and strategy modes.
- AI strategy chat using provider adapters.
- Provider support for OpenAI, Anthropic Claude, Google Gemini, Ollama, OpenRouter, Groq, xAI, Mistral, and custom OpenAI-compatible endpoints.
- League and rival analysis when user imports or connects league/team data.
- Data-health and provenance UI.
- Full test suite and CI-ready commands.
- Legal/privacy guardrails.

## Non-goals for v1

These are intentionally excluded even though the rest of the product is polished:

- No automatic transfer execution on the official fantasy site.
- No use of official Formula 1 logos, official app branding, driver headshots, broadcast imagery, or proprietary media.
- No training/fine-tuning models on Formula 1-owned content.
- No hosted default telemetry.
- No gambling or betting recommendations.

## Implementation principles

- **Deterministic core, AI shell.** Optimizer and rules engine decide. AI explains.
- **Local-first.** The app should work on a laptop with a local DuckDB database.
- **Adapter-based.** Every external service sits behind a port/interface.
- **Snapshot everything.** Decisions must be reproducible from stored snapshots.
- **Make uncertainty visible.** Recommendations include confidence, assumptions, and what would change the answer.
- **Fail gracefully.** Broken connector means degraded data, not a broken product.
- **Source-aware.** Every data point used in a recommendation must be traceable.

## Primary user journeys

### Journey A — First run

1. User launches app with Docker Compose.
2. User opens setup wizard.
3. User chooses AI provider and enters key/base URL or chooses local Ollama.
4. User imports fantasy team manually or configures a read-only session token.
5. App syncs race and fantasy data.
6. App shows dashboard with data-health badges.
7. App generates baseline recommendations.

### Journey B — Race-week strategy

1. User opens Race Week page.
2. App shows next race, lock/deadline fields, session status, weather, news, and fantasy team state.
3. User selects strategy mode: safe, balanced, aggressive, budget-builder, differential, chip-optimized.
4. Optimizer returns ranked legal options.
5. AI explains the top choices and tradeoffs.
6. User manually applies chosen moves on official fantasy platform.
7. User marks moves as applied or imports updated team state.

### Journey C — League chase

1. User imports league/rival data.
2. App compares user team against rivals.
3. App identifies common picks, differentials, risk exposure, and catch-up scenarios.
4. Optimizer can favor differential/upside strategy.
5. AI produces a league-specific plan.

## Implementation output expected

The implementation agent should produce:

- production-ready monorepo scaffold;
- pinned dependency files;
- database migrations/initialization scripts;
- typed API server;
- polished web app;
- tests and fixtures;
- connector adapters with fallback paths;
- prompt templates and provider adapters;
- documentation and examples;
- CI workflow.


<!-- END docs/00_IMPLEMENTATION_AGENT_BRIEF.md -->


---

<!-- BEGIN docs/01_PRD.md -->

# 01 — Product Requirements Document

## 1. Product name

Working/public name: **RaceWeek Strategist**.

Repository slug: `raceweek-strategist`.

Product description: an unofficial, open-source fantasy motorsport strategy assistant for fans who want a data-driven, AI-explained way to manage race-week fantasy lineups.

## 2. Problem

Fantasy motorsport players must make weekly decisions under uncertainty:

- which drivers and constructors to select;
- whether to use free transfers or take transfer penalties;
- whether to deploy one-time chips;
- whether to chase expected points, price growth, safety, or league differentials;
- how to react to practice, qualifying, penalties, weather, DNFs, and news;
- how to interpret price movements and changing asset value.

Existing fantasy interfaces show team state and scoring, but they do not provide a transparent strategy engine that combines rules, projections, optimization, data health, and explainable AI.

## 3. Target users

### Persona 1 — Competitive private-league player

- Wants to beat friends or coworkers.
- Cares about differential picks and risk-reward decisions.
- Needs recommendations that explain upside/downside.

### Persona 2 — Data-driven fan

- Watches sessions and consumes stats.
- Wants a single place to combine fantasy, performance, weather, and news signals.
- Cares about provenance and explainability.

### Persona 3 — Casual player who wants help

- Does not want to build spreadsheets.
- Wants one or two clear recommended actions each race week.
- Needs plain-language explanations.

### Persona 4 — Open-source contributor

- Wants to add projection models, connectors, visualizations, or providers.
- Needs clean architecture and good tests.

## 4. Goals

- Provide race-week recommendations that are mathematically legal and explainable.
- Support all major AI providers through bring-your-own-key configuration.
- Make all recommendations reproducible from saved data snapshots.
- Allow community extension without sacrificing correctness.
- Avoid legal and branding risk by remaining unofficial, data-source-aware, and conservative with third-party IP.

## 5. Product requirements

### PRD-001: Setup wizard

The app must guide users through:

- choosing local-only or optional hosted configuration;
- selecting AI provider;
- configuring provider key/base URL/model;
- importing or connecting fantasy team state;
- validating data-source health;
- creating first baseline projection and recommendation run.

Acceptance criteria:

- setup can be completed without any paid service if using local Ollama and manual import;
- missing AI provider does not block deterministic optimizer use;
- broken fantasy connector shows manual import fallback;
- secrets are not logged.

### PRD-002: Dashboard

Dashboard must show:

- next race/weekend;
- countdown/deadline field when available;
- user teams;
- cost cap and remaining budget;
- free transfers and transfer penalties;
- chip availability;
- current projected score;
- current strategy recommendation;
- data-health cards.

Acceptance criteria:

- every displayed recommendation links to its source snapshot and run ID;
- every data card has loading, empty, stale, and error states.

### PRD-003: Fantasy market

Market table must show drivers and constructors with:

- name, type, team/constructor;
- current price;
- recent fantasy score fields;
- price movement fields when available;
- ownership/selection fields when available;
- projected points;
- points per million;
- risk score;
- recommendation tags.

Acceptance criteria:

- table supports sorting, filtering, pinning, and comparison;
- user can compare any two drivers or constructors;
- missing upstream fields show `unknown`, not fake values.

### PRD-004: Transfer optimizer

Optimizer must return ranked recommendations under multiple strategy modes:

- safe;
- balanced;
- aggressive;
- budget-builder;
- differential;
- chip-optimized;
- custom weights.

Acceptance criteria:

- all recommendations satisfy lineup, cap, transfer, and chip constraints;
- every option includes expected gross points, transfer cost, net points, budget after move, confidence, risk, assumptions, and rationale;
- recommendations are reproducible by run ID.

### PRD-005: Chip simulator

Chip simulator must model:

- regular 2x/DRS boost;
- 3x/extra boost;
- Autopilot;
- No Negative;
- Wildcard;
- Limitless;
- Final Fix.

Acceptance criteria:

- chip rules live in rules engine, not prompt text;
- optimizer can compare no-chip vs chip scenarios;
- chip recommendations include “use now” and “save for later” rationale.

### PRD-006: Race-week intelligence

Race-week page must show:

- meetings/races;
- sessions;
- practice, qualifying, sprint, and race result summaries when available;
- weather observations and forecast fields when available;
- race-control messages and penalties when available;
- pit-stop summary when available;
- news flags and summaries.

Acceptance criteria:

- session data can come from OpenF1/FastF1/Jolpica adapters;
- data source and freshness are visible;
- stale session data does not silently feed projections without warning.

### PRD-007: AI strategy chat

Chat must answer strategy questions using read-only tools:

- get current team;
- get fantasy market snapshot;
- run optimizer;
- compare recommendations;
- summarize news;
- explain rules;
- explain assumptions.

Acceptance criteria:

- AI responses include recommendation IDs or data snapshot IDs when discussing specific decisions;
- AI must not claim certainty where data is missing;
- AI must not submit transfers;
- AI must not request passwords.

### PRD-008: League analysis

When league/rival data exists, app must show:

- league rank and gap;
- rival team overlap;
- high-owned picks;
- differential opportunities;
- catch-up scenarios;
- risk exposure relative to rivals.

Acceptance criteria:

- league analysis degrades gracefully if only partial league data is imported;
- differential optimizer mode can use league context.

### PRD-009: Data provenance and health

App must track:

- source;
- connector version;
- fetched timestamp;
- normalized table;
- snapshot hash;
- stale/error state;
- license/legal notes where relevant.

Acceptance criteria:

- user can open a data-health page and see the status of every connector;
- recommendations display stale-data warnings.

### PRD-010: Open-source contributor experience

Repository must include:

- clear setup;
- docs;
- examples;
- fixtures;
- tests;
- provider adapter guide;
- connector adapter guide;
- projection model guide;
- contribution and security policy.

Acceptance criteria:

- fresh clone can run demo mode without live secrets;
- CI can run with fixtures only.

## 6. Success metrics

Because v1 is open-source and local-first, do not add telemetry by default. Recommended opt-in metrics for maintainers:

- GitHub stars/forks;
- issue quality and contributor count;
- release downloads;
- docs completion rate from GitHub analytics if available;
- user-reported recommendation usefulness;
- test coverage and connector health.

## 7. Risks

- Fantasy API instability.
- Legal/IP restrictions around Formula 1 content.
- Users expecting exact predictions.
- AI hallucinations.
- Provider API changes.
- Supply-chain dependency compromise.

Mitigations are described in security, legal, connector, and testing documents.


<!-- END docs/01_PRD.md -->


---

<!-- BEGIN docs/02_PRODUCT_SCOPE_FEATURES.md -->

# 02 — Product Scope and Feature Inventory

## Scope rule

All features listed in this document are in v1 unless explicitly marked as excluded. The implementation plan sequences delivery, but does not defer these features out of v1.

## Feature map

### A. Setup and configuration

| Feature | v1 status | Notes |
|---|---:|---|
| Docker Compose local run | Required | `web` + `api` + local DuckDB volume |
| Setup wizard | Required | Provider, team import, data health |
| BYO AI key | Required | No built-in paid account |
| Local Ollama option | Required | Works without paid AI provider |
| Demo mode | Required | Uses fixtures only, no secrets |
| Data-source health page | Required | Shows source status and stale data |
| Export/import app settings | Required | Secrets excluded |

### B. Fantasy data

| Feature | v1 status | Notes |
|---|---:|---|
| Manual team import | Required | JSON and CSV |
| Manual market import | Required | JSON and CSV fallback |
| Optional authenticated fantasy connector | Required | Read-only; user-provided token/session only |
| Asset prices | Required | Snapshot and trend history |
| Asset scores | Required | Snapshot and trend history |
| User teams | Required | Up to three fantasy teams |
| Transfer allowance | Required | Rules engine configurable |
| Chip state | Required | User-managed or connector-derived |
| League data | Required | If imported/available |
| Auto-transfer execution | Excluded | Legal/ToS risk; not in v1 |

### C. Race and session data

| Feature | v1 status | Notes |
|---|---:|---|
| Race calendar | Required | Jolpica/FastF1/OpenF1 sources |
| Session results | Required | FP/Quali/Sprint/Race where available |
| Weather observations | Required | OpenF1 weather; future forecast optional through configurable provider |
| Race-control messages | Required | OpenF1 when available |
| Pit stop summary | Required | OpenF1/FastF1 |
| Telemetry-derived features | Required | Basic pace and position features; avoid heavy UI telemetry replay in v1 |
| Live streaming UI | Optional within v1 | Polling is enough; websockets not required |

### D. Market and analytics

| Feature | v1 status | Notes |
|---|---:|---|
| Asset market table | Required | Price, form, value, risk, projections |
| Compare assets | Required | Side-by-side comparison |
| Price movement model | Required | Transparent heuristic from available data |
| Points-per-million | Required | Asset value metric |
| Risk score | Required | DNF/reliability/news/weather flags |
| Ownership/differential score | Required | Use imported/available data |
| Data freshness badges | Required | Per table/card |

### E. Projection engine

| Feature | v1 status | Notes |
|---|---:|---|
| Baseline projection model | Required | Transparent weighted model |
| Configurable model weights | Required | User-editable advanced settings |
| Confidence intervals | Required | P10/P50/P90 or low/median/high |
| Feature importance/explanation | Required | Simple contribution breakdown |
| Model backtesting | Required | Historical/fixture backtest page |
| ML model plugin interface | Required | Default remains deterministic/transparent |

### F. Optimizer

| Feature | v1 status | Notes |
|---|---:|---|
| Legal lineup optimizer | Required | 5 drivers + 2 constructors, configurable rules |
| Transfer penalty modeling | Required | Net transfer counting |
| Budget cap constraints | Required | With Limitless exception |
| Chip simulation | Required | All known chips listed in rules doc |
| Strategy modes | Required | Safe, balanced, aggressive, budget, differential, chip |
| Ranked recommendation cards | Required | Not one opaque answer |
| What-if optimizer | Required | User can lock/ban assets |
| Explainable scoring | Required | Gross, penalties, risk, confidence |

### G. AI assistant

| Feature | v1 status | Notes |
|---|---:|---|
| Provider registry | Required | OpenAI, Anthropic, Gemini, Ollama, OpenRouter, Groq, xAI, Mistral, custom OpenAI-compatible |
| Strategy chat | Required | Tool-using, read-only |
| Recommendation explanation | Required | Based on optimizer output |
| News summarization | Required | Store metadata and short summaries |
| Compare plans | Required | User can ask “safe vs aggressive?” |
| Prompt/eval fixtures | Required | Prevent regressions |
| Streaming responses | Required | For providers that support it; fallback non-streaming |

### H. UI/UX

| Feature | v1 status | Notes |
|---|---:|---|
| Polished dashboard | Required | Desktop-first, responsive tablet/mobile |
| Dark mode | Required | Motorsport-inspired but not official branding |
| Race-week timeline | Required | Sessions and lock deadlines |
| Recommendation cards | Required | Explainable, compareable |
| Data-health page | Required | Connector status |
| Settings/provider page | Required | BYO AI and data config |
| Accessibility | Required | Keyboard nav, contrast, semantic UI |
| Empty/error/loading states | Required | All major views |

### I. Operations and open-source

| Feature | v1 status | Notes |
|---|---:|---|
| CI | Required | Lint, typecheck, unit, API, UI, E2E |
| Test fixtures | Required | No live API needed in CI |
| Release process | Required | Versioned docs/changelog |
| Contributor guide | Required | Plugin patterns |
| Security policy | Required | Vulnerability reporting |
| License | Required | Apache-2.0 recommended |


<!-- END docs/02_PRODUCT_SCOPE_FEATURES.md -->


---

<!-- BEGIN docs/03_TECH_STACK_AND_VERSIONS.md -->

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


<!-- END docs/03_TECH_STACK_AND_VERSIONS.md -->


---

<!-- BEGIN docs/04_ARCHITECTURE.md -->

# 04 — System Architecture

## Architectural style

Use a hexagonal/ports-and-adapters architecture.

```text
                 ┌──────────────────────┐
                 │      Web UI          │
                 │  Next.js / React     │
                 └──────────┬───────────┘
                            │ HTTP/OpenAPI
                 ┌──────────▼───────────┐
                 │      API Layer       │
                 │ FastAPI Controllers  │
                 └──────────┬───────────┘
                            │ use cases
┌───────────────────────────▼───────────────────────────┐
│                    Domain Core                         │
│ Rules • Projections • Optimizer • Recommendations      │
│ Pure functions where possible                          │
└───────────────┬───────────────┬───────────────┬────────┘
                │               │               │
        ┌───────▼───────┐ ┌────▼─────┐ ┌──────▼──────┐
        │ Data Ports    │ │ AI Ports │ │ Storage Port │
        └───────┬───────┘ └────┬─────┘ └──────┬──────┘
                │              │              │
┌───────────────▼─────────┐ ┌──▼────────────┐ ┌▼──────────┐
│ Connectors              │ │ Provider SDKs │ │ DuckDB     │
│ Fantasy/OpenF1/Jolpica  │ │ OpenAI/etc.   │ │ snapshots  │
└─────────────────────────┘ └───────────────┘ └───────────┘
```

## Monorepo structure

```text
raceweek-strategist/
  apps/
    api/
      src/raceweek/
        api/                 # FastAPI routers and dependencies
        core/                # pure domain logic
        connectors/          # external data adapters
        storage/             # DuckDB repository implementations
        agents/              # provider adapters and tool orchestration
        jobs/                # sync jobs and schedulers
        settings.py
      tests/
    web/
      app/
      components/
      lib/
      tests/
  packages/
    contracts/               # shared JSON schema, generated TS types
    fixtures/                # safe demo data
    ui/                      # reusable UI primitives if needed
  docs/
  api/
    openapi.yaml
  schemas/
  data/
    .gitkeep                 # local DuckDB lives here, gitignored
  docker-compose.yml
  Makefile
```

## Logical modules

### 1. Rules engine

Owns fantasy game constraints:

- lineup composition;
- budget/cost cap;
- transfer allowances;
- transfer penalties;
- net-transfer counting;
- chip effects;
- deadline/lock handling;
- scoring-rule configuration.

Rules are versioned by season and game version.

### 2. Data ingestion

Owns fetching, caching, raw snapshot storage, normalization, and data health.

Connectors:

- fantasy connector;
- manual import connector;
- OpenF1 connector;
- Jolpica connector;
- FastF1 adapter;
- RSS/news connector;
- weather connector if separate from OpenF1.

### 3. Feature engine

Transforms normalized data into model-ready features:

- rolling fantasy points;
- rolling price deltas;
- points per million;
- qualifying form;
- race pace indicators;
- teammate deltas;
- constructor reliability;
- DNF/penalty risk;
- weather/race-control risk;
- ownership/differential score.

### 4. Projection engine

Produces transparent expected points and uncertainty bands for each asset and event.

Default v1 projection model:

- weighted heuristic model;
- configurable weights;
- feature contribution breakdown;
- no opaque LLM predictions.

### 5. Optimizer

Produces legal recommendations using projections, rules, risk preferences, and strategy mode weights.

Output is ranked recommendation options with:

- proposed transfers;
- chip action;
- expected gross points;
- transfer penalty;
- net expected points;
- budget after move;
- risk;
- confidence;
- assumptions;
- explanation payload for AI.

### 6. AI agent layer

The agent layer exposes read-only tools to the LLM. The LLM may ask the deterministic services for calculations and then explain them.

Provider adapters implement a common interface:

```python
class AiProvider(Protocol):
    async def complete(self, request: ChatCompletionRequest) -> ChatCompletionResponse: ...
    async def stream(self, request: ChatCompletionRequest) -> AsyncIterator[ChatCompletionChunk]: ...
    async def list_models(self) -> list[ModelInfo]: ...
```

### 7. API layer

FastAPI exposes typed endpoints documented in `api/openapi.yaml`. Controllers must remain thin and call use cases.

### 8. Web UI

Next.js web app consumes the API and handles:

- setup wizard;
- dashboard;
- market;
- optimizer;
- race week;
- league analysis;
- AI chat;
- settings;
- data health.

## Data flow

```text
External APIs / manual files
  → raw source_snapshots
  → normalized domain tables
  → feature tables
  → projection runs
  → optimizer runs
  → recommendation options
  → AI explanation/chat
  → UI
```

## Snapshot and reproducibility requirement

Every recommendation must be reproducible.

For each recommendation run store:

- run ID;
- timestamp;
- source snapshot IDs;
- fantasy rules version;
- projection model version;
- optimizer version;
- strategy mode and weights;
- request payload;
- ranked output payload;
- AI explanation metadata, if any.

## Error handling architecture

External data failures must produce structured degraded states:

```json
{
  "source": "openf1",
  "status": "degraded",
  "severity": "warning",
  "message": "Weather endpoint unavailable; using last successful snapshot from 2026-06-05T12:00:00Z",
  "lastSuccessfulSyncAt": "2026-06-05T12:00:00Z"
}
```

Do not allow connector exceptions to crash the dashboard.

## Security boundaries

- Browser never receives provider API keys.
- API logs redact headers and secrets.
- Provider requests include only the minimum relevant strategy context.
- Stored raw snapshots must not include authentication tokens.
- User can delete all local data.

## Extensibility points

- `FantasyDataProvider`
- `RaceDataProvider`
- `NewsProvider`
- `ProjectionModel`
- `OptimizerStrategy`
- `AiProvider`
- `UiPlugin` later, but not necessary in v1.


<!-- END docs/04_ARCHITECTURE.md -->


---

<!-- BEGIN docs/05_DATA_SOURCES_AND_CONNECTORS.md -->

# 05 — Data Sources and Connectors

## Source strategy

The app must not rely on a single fragile data source. Use adapters with explicit provenance, caching, and fallback.

Data source priority:

1. User manual import when authenticated sources are unavailable or legally uncertain.
2. Read-only fantasy connector using user-provided session/token when user opts in.
3. Public motorsport data APIs for race/session context.
4. RSS/news feeds for headlines and short summaries.
5. Fixture/demo data for tests and demos.

## Connector rules

Every connector must:

- implement a typed port/interface;
- save raw snapshots before normalization;
- save source metadata and response hash;
- use rate limits and retries;
- never log secrets;
- degrade gracefully;
- include contract tests using fixtures or mocked HTTP;
- expose a data-health status.

## Fantasy data connector

### Important status

The fantasy game API is not treated as a stable official public API. It is an optional read-only connector. The product must work with manual import even if this connector breaks.

### Known base URL

Community documentation describes this REST base URL:

```text
https://fantasy-api.formula1.com/partner_games/f1
```

The game-version segment has historically appeared as `2022` in documented paths. Do **not** hardcode that value in code; configure it:

```env
FANTASY_API_BASE_URL=https://fantasy-api.formula1.com/partner_games/f1
FANTASY_GAME_VERSION=2022
```

### Documented endpoints to support

These paths are documented by community/third-party sources and must be implemented through a configurable endpoint map:

| Resource | Method | Path template | Data selector | Required? |
|---|---|---|---|---:|
| players | GET | `{game_version}/players` | `players` | Yes |
| teams | GET | `{game_version}/teams` | `teams` | Yes |
| leaderboards | GET | `{game_version}/leaderboards/leagues?league_id={league_id}` | `leaderboards` | Yes, when league ID exists |
| live_stats | GET | `{game_version}/live_stats?game_period_id={game_period_id}` | `live_stats` | Yes |
| picked_teams | GET | `{game_version}/picked_teams/for_slot?game_period_id={game_period_id}&slot={slot}&user_global_id={user_global_id}` | `picked_teams` | Yes, when authenticated/imported context exists |

### Authentication approach

v1 must not ask for or store the user's official account password.

Allowed v1 approaches:

- manual import;
- user-pasted session/bearer token in local `.env` or local settings;
- browser-devtools token extraction instructions in docs, clearly marked advanced and user-responsibility;
- local-only encrypted storage if UI entry is implemented.

Disallowed in v1:

- automated login with username/password;
- scraping browser cookies without explicit user action;
- submitting transfers;
- bypassing rate limits or anti-bot controls.

### Fantasy connector port

```python
class FantasyDataProvider(Protocol):
    async def get_assets(self) -> list[FantasyAssetRaw]: ...
    async def get_constructors(self) -> list[FantasyConstructorRaw]: ...
    async def get_live_stats(self, game_period_id: str) -> FantasyLiveStatsRaw: ...
    async def get_league_leaderboard(self, league_id: str) -> FantasyLeaderboardRaw: ...
    async def get_picked_team(self, game_period_id: str, slot: int, user_global_id: str) -> FantasyPickedTeamRaw: ...
    async def health(self) -> DataSourceStatus: ...
```

### Manual import

Manual import is a first-class connector, not a fallback afterthought.

Supported formats:

- `fantasy_team.json`
- `fantasy_market_snapshot.json`
- `fantasy_scores.csv`
- `fantasy_league.csv`

Required import validation:

- schema validation;
- asset type validation;
- price numeric validation;
- no duplicate lineup assets;
- budget legality validation;
- warnings for unknown fields, not failure.

## OpenF1 connector

Use OpenF1 for recent/historical race-week context from 2023 onward.

Recommended base URL:

```text
https://api.openf1.org/v1
```

OpenF1 endpoints to support in v1:

| Endpoint | Use |
|---|---|
| `/meetings` | Race calendar/meetings |
| `/sessions` | FP/Quali/Sprint/Race sessions |
| `/drivers` | Driver metadata |
| `/session_result` | Session classification/results |
| `/starting_grid` | Grid context |
| `/position` | Position changes |
| `/laps` | Lap/pace features |
| `/stints` | Tyre/stint features |
| `/pit` | Pit-stop summary |
| `/race_control` | flags, penalties, incidents |
| `/weather` | observed session weather |
| `/championship` | standings context where available |

Rate limits and data availability must be configurable. The free historical API should be treated as rate-limited. Cache aggressively.

## Jolpica connector

Use Jolpica as an Ergast-compatible source for schedules, results, qualifying, sprint, standings, and historical context.

Recommended base URL:

```text
https://api.jolpi.ca/ergast/f1
```

Use Jolpica for:

- race calendar;
- race results;
- qualifying results;
- sprint results;
- driver standings;
- constructor standings;
- historical backtesting data.

## FastF1 adapter

Use FastF1 for Python-based data access and feature engineering where it adds value:

- schedules;
- session results;
- timing data;
- telemetry-derived features;
- caching;
- fallback to Jolpica-derived historical results.

Do not expose raw heavy telemetry in v1 UI unless needed for features. Store aggregated features, not large raw telemetry blobs by default.

## News connector

### Purpose

News helps flag uncertainty. It must not become a copyright-risk content mirror.

Supported v1 news ingestion:

- RSS/Atom feeds configured by user/maintainer;
- official article metadata when allowed;
- title, source, URL, published time, summary snippet, extracted entities;
- AI-generated short summary from retrieved permitted text or feed summary;
- manual user-added news note.

Disallowed:

- storing full copyrighted articles by default;
- bypassing paywalls;
- copying images;
- training models on scraped articles;
- using news content without provenance.

### News item schema

```json
{
  "id": "news_...",
  "source": "rss:f1-news-example",
  "title": "string",
  "url": "string",
  "publishedAt": "datetime",
  "retrievedAt": "datetime",
  "summary": "short generated or feed-provided summary",
  "entities": ["driver:...", "constructor:..."],
  "riskFlags": ["grid_penalty", "illness", "upgrade", "reliability"],
  "licenseNote": "metadata-only"
}
```

## Weather

v1 uses OpenF1 observed weather for sessions. Future forecasts are optional and should be configured through a generic weather provider interface.

If forecast is absent, do not invent it. Use `unknown` and show a UI warning.

## Data health statuses

Allowed statuses:

- `ok`
- `stale`
- `degraded`
- `error`
- `disabled`
- `unknown`

Each status includes:

- source;
- last successful sync;
- last attempted sync;
- freshness seconds;
- rate-limit status;
- error code/message;
- user-action message.

## Caching policy

| Data type | Race-week TTL | Off-week TTL | Notes |
|---|---:|---:|---|
| Fantasy market | 15 min | 6 hr | Prices/scores can change after events |
| User team | 5 min | 1 hr | Manual refresh allowed |
| Race calendar | 24 hr | 7 days | Low volatility |
| Session results | 2 min during live session | immutable after final + 12 hr | Mark provisional/final |
| Weather observations | 2 min during live session | immutable after final | Observed weather only |
| News feeds | 10 min | 30 min | Respect feed cache headers |
| Provider models | 24 hr | 24 hr | Not critical |

## Connector implementation pattern

```python
@dataclass(frozen=True)
class ConnectorResult[T]:
    source: str
    fetched_at: datetime
    raw_snapshot_id: str
    data: T
    status: DataSourceStatus

class BaseHttpConnector:
    async def fetch_json(self, request: ConnectorRequest) -> ConnectorResult[dict]:
        # 1. apply rate limit
        # 2. call with httpx
        # 3. redact secrets in logs
        # 4. save raw snapshot
        # 5. return typed result
        ...
```

## Data provenance record

Every raw fetch creates a row in `source_snapshots`:

```text
snapshot_id
source_name
source_version
request_method
request_url_template
request_params_json
fetched_at
http_status
content_hash
raw_storage_path
license_note
normalization_version
error_message
```

Never store authorization headers or tokens.


<!-- END docs/05_DATA_SOURCES_AND_CONNECTORS.md -->


---

<!-- BEGIN docs/06_DOMAIN_MODEL_DATABASE_SCHEMA.md -->

# 06 — Domain Model and Database Schema

## Storage choice

Use DuckDB as the default local analytical database.

Recommended local file:

```text
./data/raceweek.duckdb
```

Migrations can be simple SQL files applied in lexicographic order:

```text
apps/api/src/raceweek/storage/migrations/
  0001_init.sql
  0002_recommendations.sql
  0003_agent_messages.sql
```

## Naming conventions

- Table names: plural snake_case.
- Primary keys: text IDs generated by application, e.g. `asset_...`, `run_...`.
- Timestamps: UTC ISO semantics, stored as `TIMESTAMP`.
- JSON: use DuckDB `JSON` type where suitable.
- Raw external payloads: store compressed file path or JSON depending size.

## Core entities

```text
FantasyAsset
FantasyTeamSnapshot
FantasyRuleset
RaceMeeting
RaceSession
SessionResult
WeatherObservation
NewsItem
ProjectionRun
Projection
RecommendationRun
RecommendationOption
AgentConversation
ProviderConfig
DataSourceStatus
```

## DuckDB schema

```sql
CREATE TABLE IF NOT EXISTS source_snapshots (
  snapshot_id TEXT PRIMARY KEY,
  source_name TEXT NOT NULL,
  source_version TEXT NOT NULL,
  connector_version TEXT NOT NULL,
  request_method TEXT NOT NULL,
  request_url_template TEXT NOT NULL,
  request_params_json JSON,
  fetched_at TIMESTAMP NOT NULL,
  http_status INTEGER,
  content_hash TEXT NOT NULL,
  raw_storage_path TEXT,
  raw_json JSON,
  license_note TEXT,
  normalization_version TEXT NOT NULL,
  status TEXT NOT NULL,
  error_message TEXT
);

CREATE TABLE IF NOT EXISTS fantasy_events (
  event_id TEXT PRIMARY KEY,
  season INTEGER NOT NULL,
  game_period_id TEXT,
  round_number INTEGER,
  meeting_key TEXT,
  name TEXT NOT NULL,
  starts_at TIMESTAMP,
  locks_at TIMESTAMP,
  status TEXT NOT NULL DEFAULT 'scheduled',
  source_snapshot_id TEXT
);

CREATE TABLE IF NOT EXISTS fantasy_assets (
  asset_id TEXT PRIMARY KEY,
  external_id TEXT,
  asset_type TEXT NOT NULL CHECK (asset_type IN ('driver', 'constructor')),
  display_name TEXT NOT NULL,
  short_name TEXT,
  constructor_name TEXT,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  metadata_json JSON,
  first_seen_at TIMESTAMP NOT NULL,
  last_seen_at TIMESTAMP NOT NULL,
  source_snapshot_id TEXT
);

CREATE TABLE IF NOT EXISTS fantasy_asset_prices (
  price_id TEXT PRIMARY KEY,
  asset_id TEXT NOT NULL,
  event_id TEXT,
  price_millions DOUBLE NOT NULL,
  price_delta_millions DOUBLE,
  price_change_probability DOUBLE,
  captured_at TIMESTAMP NOT NULL,
  source_snapshot_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fantasy_asset_scores (
  score_id TEXT PRIMARY KEY,
  asset_id TEXT NOT NULL,
  event_id TEXT NOT NULL,
  fantasy_points DOUBLE,
  score_breakdown_json JSON,
  ownership_pct DOUBLE,
  selected_by_pct DOUBLE,
  captured_at TIMESTAMP NOT NULL,
  source_snapshot_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_profiles (
  user_id TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL,
  settings_json JSON
);

CREATE TABLE IF NOT EXISTS user_fantasy_teams (
  team_snapshot_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  external_team_id TEXT,
  slot INTEGER,
  team_name TEXT NOT NULL,
  event_id TEXT,
  cost_cap_millions DOUBLE NOT NULL,
  budget_used_millions DOUBLE NOT NULL,
  budget_remaining_millions DOUBLE NOT NULL,
  free_transfers INTEGER NOT NULL,
  transfer_penalty_points DOUBLE NOT NULL DEFAULT 10,
  captured_at TIMESTAMP NOT NULL,
  source_snapshot_id TEXT,
  is_current BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS user_team_assets (
  team_snapshot_id TEXT NOT NULL,
  asset_id TEXT NOT NULL,
  asset_type TEXT NOT NULL,
  boost_multiplier DOUBLE DEFAULT 1,
  is_captain_boost BOOLEAN DEFAULT FALSE,
  PRIMARY KEY (team_snapshot_id, asset_id)
);

CREATE TABLE IF NOT EXISTS chip_states (
  chip_state_id TEXT PRIMARY KEY,
  team_snapshot_id TEXT NOT NULL,
  chip_name TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('available', 'used', 'active', 'unavailable', 'unknown')),
  used_event_id TEXT,
  metadata_json JSON
);

CREATE TABLE IF NOT EXISTS transfers (
  transfer_id TEXT PRIMARY KEY,
  team_snapshot_id TEXT NOT NULL,
  event_id TEXT,
  asset_out_id TEXT,
  asset_in_id TEXT,
  applied BOOLEAN NOT NULL DEFAULT FALSE,
  source TEXT NOT NULL CHECK (source IN ('manual', 'recommendation', 'import')),
  created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS meetings (
  meeting_key TEXT PRIMARY KEY,
  season INTEGER NOT NULL,
  round_number INTEGER,
  meeting_name TEXT NOT NULL,
  circuit_name TEXT,
  country_name TEXT,
  location TEXT,
  date_start TIMESTAMP,
  date_end TIMESTAMP,
  source_snapshot_id TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
  session_key TEXT PRIMARY KEY,
  meeting_key TEXT NOT NULL,
  session_name TEXT NOT NULL,
  session_type TEXT NOT NULL,
  starts_at TIMESTAMP,
  ends_at TIMESTAMP,
  status TEXT NOT NULL DEFAULT 'scheduled',
  source_snapshot_id TEXT
);

CREATE TABLE IF NOT EXISTS session_results (
  result_id TEXT PRIMARY KEY,
  session_key TEXT NOT NULL,
  driver_number TEXT,
  driver_name TEXT,
  constructor_name TEXT,
  position INTEGER,
  classified_position TEXT,
  grid_position INTEGER,
  points DOUBLE,
  result_json JSON,
  source_snapshot_id TEXT
);

CREATE TABLE IF NOT EXISTS pit_stops (
  pit_stop_id TEXT PRIMARY KEY,
  session_key TEXT NOT NULL,
  driver_number TEXT,
  lap_number INTEGER,
  pit_duration_seconds DOUBLE,
  source_snapshot_id TEXT
);

CREATE TABLE IF NOT EXISTS race_control_messages (
  message_id TEXT PRIMARY KEY,
  session_key TEXT NOT NULL,
  category TEXT,
  flag TEXT,
  driver_number TEXT,
  lap_number INTEGER,
  message TEXT NOT NULL,
  occurred_at TIMESTAMP,
  source_snapshot_id TEXT
);

CREATE TABLE IF NOT EXISTS weather_observations (
  weather_id TEXT PRIMARY KEY,
  session_key TEXT NOT NULL,
  observed_at TIMESTAMP NOT NULL,
  air_temperature DOUBLE,
  track_temperature DOUBLE,
  rainfall DOUBLE,
  humidity DOUBLE,
  wind_speed DOUBLE,
  wind_direction DOUBLE,
  pressure DOUBLE,
  source_snapshot_id TEXT
);

CREATE TABLE IF NOT EXISTS news_items (
  news_id TEXT PRIMARY KEY,
  source_name TEXT NOT NULL,
  title TEXT NOT NULL,
  url TEXT NOT NULL,
  published_at TIMESTAMP,
  retrieved_at TIMESTAMP NOT NULL,
  summary TEXT,
  entities_json JSON,
  risk_flags_json JSON,
  license_note TEXT,
  source_snapshot_id TEXT
);

CREATE TABLE IF NOT EXISTS features_asset_event (
  feature_id TEXT PRIMARY KEY,
  asset_id TEXT NOT NULL,
  event_id TEXT NOT NULL,
  generated_at TIMESTAMP NOT NULL,
  feature_version TEXT NOT NULL,
  rolling_points_3 DOUBLE,
  rolling_points_5 DOUBLE,
  points_per_million DOUBLE,
  price_delta_3 DOUBLE,
  quali_form DOUBLE,
  race_pace_form DOUBLE,
  teammate_delta DOUBLE,
  reliability_score DOUBLE,
  penalty_risk DOUBLE,
  weather_risk DOUBLE,
  news_risk DOUBLE,
  ownership_pct DOUBLE,
  differential_score DOUBLE,
  features_json JSON
);

CREATE TABLE IF NOT EXISTS projection_runs (
  projection_run_id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL,
  model_name TEXT NOT NULL,
  model_version TEXT NOT NULL,
  generated_at TIMESTAMP NOT NULL,
  source_snapshot_ids_json JSON NOT NULL,
  config_json JSON NOT NULL,
  status TEXT NOT NULL,
  error_message TEXT
);

CREATE TABLE IF NOT EXISTS projections (
  projection_id TEXT PRIMARY KEY,
  projection_run_id TEXT NOT NULL,
  asset_id TEXT NOT NULL,
  expected_points DOUBLE NOT NULL,
  floor_points DOUBLE,
  ceiling_points DOUBLE,
  confidence DOUBLE NOT NULL,
  risk_score DOUBLE NOT NULL,
  projected_price_delta_millions DOUBLE,
  contribution_breakdown_json JSON,
  assumptions_json JSON
);

CREATE TABLE IF NOT EXISTS recommendation_runs (
  recommendation_run_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  team_snapshot_id TEXT NOT NULL,
  event_id TEXT NOT NULL,
  projection_run_id TEXT NOT NULL,
  ruleset_version TEXT NOT NULL,
  optimizer_version TEXT NOT NULL,
  strategy_mode TEXT NOT NULL,
  request_json JSON NOT NULL,
  generated_at TIMESTAMP NOT NULL,
  status TEXT NOT NULL,
  error_message TEXT
);

CREATE TABLE IF NOT EXISTS recommendation_options (
  option_id TEXT PRIMARY KEY,
  recommendation_run_id TEXT NOT NULL,
  rank INTEGER NOT NULL,
  strategy_mode TEXT NOT NULL,
  chip_action TEXT,
  expected_gross_points DOUBLE NOT NULL,
  transfer_penalty_points DOUBLE NOT NULL,
  expected_net_points DOUBLE NOT NULL,
  budget_used_millions DOUBLE NOT NULL,
  budget_remaining_millions DOUBLE NOT NULL,
  expected_budget_delta_millions DOUBLE,
  risk_score DOUBLE NOT NULL,
  confidence DOUBLE NOT NULL,
  summary TEXT NOT NULL,
  rationale_json JSON NOT NULL,
  assumptions_json JSON NOT NULL,
  warnings_json JSON
);

CREATE TABLE IF NOT EXISTS recommendation_transfers (
  option_id TEXT NOT NULL,
  sequence_number INTEGER NOT NULL,
  asset_out_id TEXT,
  asset_in_id TEXT,
  reason TEXT,
  PRIMARY KEY (option_id, sequence_number)
);

CREATE TABLE IF NOT EXISTS agent_conversations (
  conversation_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  title TEXT,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_messages (
  message_id TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('system', 'user', 'assistant', 'tool')),
  content TEXT NOT NULL,
  provider_name TEXT,
  model_name TEXT,
  tool_calls_json JSON,
  recommendation_run_id TEXT,
  created_at TIMESTAMP NOT NULL,
  redaction_status TEXT NOT NULL DEFAULT 'checked'
);

CREATE TABLE IF NOT EXISTS provider_configs (
  provider_config_id TEXT PRIMARY KEY,
  provider_name TEXT NOT NULL,
  display_name TEXT NOT NULL,
  base_url TEXT,
  default_model TEXT,
  api_key_env_var TEXT,
  enabled BOOLEAN NOT NULL DEFAULT FALSE,
  supports_streaming BOOLEAN NOT NULL DEFAULT TRUE,
  supports_tools BOOLEAN NOT NULL DEFAULT FALSE,
  config_json JSON,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS app_settings (
  setting_key TEXT PRIMARY KEY,
  setting_value_json JSON NOT NULL,
  updated_at TIMESTAMP NOT NULL
);
```

## Domain invariants

### Team composition

- A legal fantasy lineup has exactly 5 drivers and 2 constructors unless a ruleset explicitly changes it.
- No duplicate asset IDs in a lineup.
- Budget used must be less than or equal to cost cap except in Limitless simulation.

### Transfers

- Transfer count is computed as net asset changes between prior locked team and proposed team.
- Transfer penalty is `max(0, transfer_count - free_transfers) * transfer_penalty_points` unless chip rules override it.

### Recommendations

- A recommendation option must reference exactly one recommendation run.
- A recommendation run must reference exactly one projection run and one team snapshot.
- Recommendation ranking must be deterministic for the same input.

### AI messages

- AI messages can reference recommendation runs but cannot create recommendation records without an optimizer run.
- Tool messages must store tool name and sanitized input/output metadata.

## ID format

Recommended IDs:

```text
snapshot_01J...
asset_01J...
event_2026_01
team_01J...
projrun_01J...
recrun_01J...
recopt_01J...
msg_01J...
```

Use ULID-compatible sortable IDs.

## Schema migration rules

- Never mutate old migrations.
- Add new migrations for schema changes.
- Include migration tests that create a fresh DB and apply all migrations.
- Include backward-compatible readers when possible.


<!-- END docs/06_DOMAIN_MODEL_DATABASE_SCHEMA.md -->


---

<!-- BEGIN docs/07_API_DESIGN.md -->

# 07 — API Design Notes

The canonical API contract lives in `api/openapi.yaml`. This document explains conventions and implementation expectations.

## API principles

- Prefix all product endpoints with `/api/v1`.
- Return typed JSON only.
- Use ISO-8601 UTC timestamps.
- Use `snake_case` in Python internals and `camelCase` in API JSON.
- Validate all request bodies with Pydantic.
- Return stable error envelopes.
- Do not expose secrets.
- Include `runId`, `snapshotId`, or `source` fields whenever a response is derived from stored data.

## Error envelope

```json
{
  "error": {
    "code": "DATA_SOURCE_STALE",
    "message": "Fantasy market data is stale.",
    "details": {
      "source": "fantasy_api",
      "lastSuccessfulSyncAt": "2026-06-05T12:00:00Z"
    },
    "requestId": "req_..."
  }
}
```

## Pagination

Use cursor pagination for large collections:

```json
{
  "items": [],
  "nextCursor": "cursor_..."
}
```

## Endpoint groups

### Health and metadata

- `GET /health`
- `GET /api/v1/app/status`
- `GET /api/v1/data-sources/status`

### Setup and settings

- `GET /api/v1/settings`
- `PUT /api/v1/settings`
- `GET /api/v1/providers`
- `POST /api/v1/providers/test`

### Fantasy

- `POST /api/v1/fantasy/import/team`
- `POST /api/v1/fantasy/import/market`
- `POST /api/v1/fantasy/sync`
- `GET /api/v1/fantasy/assets`
- `GET /api/v1/fantasy/teams/current`
- `GET /api/v1/fantasy/rulesets/current`

### Race week

- `GET /api/v1/races`
- `GET /api/v1/races/current`
- `GET /api/v1/races/{meetingKey}/sessions`
- `GET /api/v1/races/{meetingKey}/intelligence`

### Projections and optimizer

- `POST /api/v1/projections/run`
- `GET /api/v1/projections/runs/{projectionRunId}`
- `POST /api/v1/optimizer/recommendations`
- `GET /api/v1/recommendations/runs/{recommendationRunId}`
- `GET /api/v1/recommendations/options/{optionId}`

### League

- `POST /api/v1/leagues/import`
- `GET /api/v1/leagues/{leagueId}/analysis`

### Agent

- `POST /api/v1/agent/conversations`
- `GET /api/v1/agent/conversations/{conversationId}`
- `POST /api/v1/agent/chat`

## API implementation expectations

Controllers should call use cases, not repositories directly.

Example layering:

```text
api/routes/optimizer.py
  -> use_cases/generate_recommendations.py
    -> core/rules.py
    -> core/projections.py
    -> core/optimizer.py
    -> storage/repositories.py
```

## Streaming

AI chat should support server-sent events in v1 if practical:

```text
POST /api/v1/agent/chat?stream=true
Content-Type: text/event-stream
```

Non-streaming response must always be supported.

## Idempotency

Sync and optimization endpoints should accept an optional `idempotencyKey`:

```json
{
  "idempotencyKey": "client-generated-key"
}
```

If repeated, return the existing run/result where safe.

## API security

Local mode can use no authentication by default on `localhost`, but production/hosted mode must require auth. Add a configuration flag:

```env
APP_AUTH_MODE=local_only | single_user_password | reverse_proxy
```

For v1 local mode:

- bind API to `127.0.0.1` by default;
- CORS only allows configured web origin;
- redact secrets in logs.


<!-- END docs/07_API_DESIGN.md -->


---

<!-- BEGIN docs/08_AI_PROVIDER_AGENT_ARCHITECTURE.md -->

# 08 — AI Provider and Agent Architecture

## Principle

The AI assistant is an explanation, comparison, and interaction layer over deterministic data and optimizer outputs. It is not the calculation engine.

## Required providers

v1 must support:

| Provider | Adapter strategy | Notes |
|---|---|---|
| OpenAI | Official `openai` Python SDK; Responses API where available | Use for tool-capable hosted models |
| Anthropic Claude | Official `anthropic` Python SDK | Messages API/tool use |
| Google Gemini | Official `google-genai` SDK | Developer API or Vertex-compatible config |
| Ollama | Local SDK or OpenAI-compatible endpoint | Default local option; no API key needed for local |
| OpenRouter | OpenAI-compatible chat endpoint | User supplies key and model slug |
| Groq | OpenAI-compatible endpoint | User supplies key and model |
| xAI | OpenAI-compatible endpoint | User supplies key and model |
| Mistral | Official `mistralai` SDK or OpenAI-compatible where configured | Pin safe SDK version |
| Custom OpenAI-compatible | OpenAI SDK with configurable base URL | For LM Studio, vLLM, local gateways, etc. |

## Provider configuration

Provider config must not store raw secrets. Store only env var names or local encrypted references.

Example:

```json
{
  "providerName": "openrouter",
  "displayName": "OpenRouter",
  "baseUrl": "https://openrouter.ai/api/v1",
  "defaultModel": "user-selected-model",
  "apiKeyEnvVar": "OPENROUTER_API_KEY",
  "enabled": true,
  "supportsStreaming": true,
  "supportsTools": false
}
```

## Provider interface

```python
class ChatMessage(BaseModel):
    role: Literal['system', 'user', 'assistant', 'tool']
    content: str
    tool_call_id: str | None = None

class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]

class ChatCompletionRequest(BaseModel):
    messages: list[ChatMessage]
    model: str
    tools: list[ToolDefinition] = []
    temperature: float = 0.2
    max_output_tokens: int = 4000
    stream: bool = False

class ChatCompletionResponse(BaseModel):
    content: str
    tool_calls: list[ToolCall] = []
    model: str
    provider: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: int | None = None
```

## Tool model

LLM tools are read-only. Mutating actions require explicit user confirmation in the UI and remain local-only metadata actions.

### Required tools

| Tool | Purpose | Mutates? |
|---|---|---:|
| `get_current_team` | Fetch team snapshot | No |
| `get_market_snapshot` | Fetch assets/prices/projections | No |
| `get_data_health` | Fetch connector status | No |
| `run_projection` | Create projection run | Yes, local data only |
| `run_optimizer` | Create recommendation run | Yes, local data only |
| `get_recommendation_run` | Fetch recommendations | No |
| `compare_recommendations` | Compare option IDs | No |
| `search_news` | Search stored news items | No |
| `explain_rules` | Retrieve configured rules | No |
| `get_league_analysis` | Fetch league analytics | No |

Important: `run_projection` and `run_optimizer` mutate the local database by creating runs, but they do not touch the user's fantasy account.

## Agent workflow

### Strategy question workflow

```text
User asks strategy question
  → classify intent
  → fetch current team + data health
  → run optimizer if no recent compatible run exists
  → fetch top recommendation options
  → produce explanation with assumptions/warnings
```

### News workflow

```text
User asks about news impact
  → search stored news
  → map entities to assets
  → fetch projections/recommendations
  → explain risk impact
```

### Chip workflow

```text
User asks whether to use chip
  → fetch chip state
  → simulate no-chip and chip scenarios
  → compare expected net points, risk, future opportunity cost
  → explain use/save recommendation
```

## System prompt requirements

The system prompt must include:

- unofficial tool disclaimer;
- deterministic source-of-truth rule;
- no auto-transfer rule;
- uncertainty and data freshness rule;
- concise but actionable output format;
- no API key or secret disclosure;
- no claims beyond data.

See `examples/prompts/agent-system-prompt.md`.

## AI answer format

Default recommendation answer:

```text
Recommendation: [action]
Confidence: [low/medium/high + numeric if available]
Expected impact: [gross, penalty, net]
Why: [3 bullets max]
Risks: [key risks]
What would change this: [conditions]
Data freshness: [source statuses]
```

## Hallucination controls

- The LLM cannot call external web directly in product runtime unless a provider/tool is explicitly configured.
- Use local stored data and connector snapshots.
- Always pass rules as structured JSON, not just prose.
- Require recommendation IDs in any answer that advises a transfer.
- Post-process AI response to detect banned claims:
  - “guaranteed”;
  - “official” affiliation;
  - “I made the transfer”;
  - raw secret patterns.

## Provider fallback

Provider fallback order is user-configurable. Default recommendation:

1. selected provider/model;
2. local Ollama model if configured;
3. no-AI deterministic explanation template.

The app must remain useful without AI.

## Prompt/eval testing

Create eval fixtures for:

- transfer recommendation explanation;
- chip recommendation explanation;
- missing-data warning;
- stale-data warning;
- league differential strategy;
- provider failure fallback;
- refusal to auto-submit transfers;
- refusal to claim official affiliation.

For each fixture, assert:

- includes recommendation/run IDs when applicable;
- does not invent drivers/prices;
- includes risk/data freshness where relevant;
- does not expose secrets;
- stays within output shape.


<!-- END docs/08_AI_PROVIDER_AGENT_ARCHITECTURE.md -->


---

<!-- BEGIN docs/09_OPTIMIZER_PROJECTION_ENGINE.md -->

# 09 — Optimizer and Projection Engine

## Source-of-truth hierarchy

1. Rules engine determines legality.
2. Projection engine estimates points and uncertainty.
3. Optimizer ranks legal options.
4. AI explains optimizer output.

The AI must never bypass steps 1–3.

## Rules engine

Rules must be stored as versioned JSON and loaded into typed models.

Example ruleset:

```json
{
  "rulesetId": "fantasy_2026_v1",
  "season": 2026,
  "lineup": {
    "drivers": 5,
    "constructors": 2
  },
  "budget": {
    "costCapMillions": 100.0
  },
  "transfers": {
    "freeTransfersPerRound": 2,
    "maxCarriedTransfers": 1,
    "penaltyPointsPerExtraTransfer": 10,
    "countingMode": "net_asset_changes"
  },
  "chips": [
    "2x_boost",
    "3x_boost",
    "autopilot",
    "no_negative",
    "wildcard",
    "limitless",
    "final_fix"
  ]
}
```

## Transfer counting

Implement as pure function:

```python
def calculate_net_transfers(previous_asset_ids: set[str], proposed_asset_ids: set[str]) -> int:
    removed = previous_asset_ids - proposed_asset_ids
    added = proposed_asset_ids - previous_asset_ids
    if len(removed) != len(added):
        raise InvalidLineupTransition("lineup size changed unexpectedly")
    return len(added)
```

For standard transfers:

```python
penalty = max(0, net_transfers - free_transfers) * penalty_points_per_extra_transfer
```

Chip overrides:

- Wildcard: transfer penalty becomes 0 for the event, but budget cap remains.
- Limitless: transfer penalty becomes 0 and budget cap constraint is disabled for that event; future team reversion must be represented in assumptions.
- Final Fix: one late driver change scenario; it does not change regular boost alone.
- No Negative: lower-bound score for selected assets/team is floored according to configured rules.
- Autopilot: 2x boost assigned to highest-scoring eligible driver after scoring simulation.
- 3x Boost: selected eligible driver receives 3x instead of normal boost according to ruleset.

## Projection engine

### v1 default model: transparent weighted projection

For each asset/event:

```text
expected_points =
  w_recent3 * rolling_fantasy_points_3
+ w_recent5 * rolling_fantasy_points_5
+ w_quali * qualifying_form
+ w_race_pace * race_pace_form
+ w_constructor * constructor_form
+ w_circuit * circuit_fit_score
+ w_weather * weather_adjustment
+ w_news * news_adjustment
+ w_penalty * penalty_adjustment
+ base_asset_prior
```

Default weights should be configuration, not constants scattered through code.

Example default weights:

```json
{
  "rolling_fantasy_points_3": 0.30,
  "rolling_fantasy_points_5": 0.20,
  "qualifying_form": 0.15,
  "race_pace_form": 0.15,
  "constructor_form": 0.08,
  "circuit_fit_score": 0.04,
  "weather_adjustment": 0.03,
  "news_adjustment": 0.03,
  "penalty_adjustment": 0.02
}
```

These are initial defaults. The implementation must support backtesting and user tuning.

### Projection outputs

For each asset:

- expected points;
- floor/P10;
- ceiling/P90;
- confidence;
- risk score;
- projected price delta;
- contribution breakdown;
- assumptions.

### Confidence calculation

Confidence should decrease when:

- data is stale;
- session data is missing;
- news risk is high;
- weather risk is high;
- asset has high DNF/penalty variance;
- projection model has low historical accuracy for similar events.

## Feature engineering

Required v1 features:

| Feature | Description |
|---|---|
| `rolling_points_3` | Rolling average over last 3 fantasy events |
| `rolling_points_5` | Rolling average over last 5 fantasy events |
| `points_per_million` | Expected points divided by price |
| `price_delta_3` | Recent price change trend |
| `quali_form` | Recent qualifying/session rank feature |
| `race_pace_form` | Recent race/lap/session pace feature |
| `constructor_form` | Constructor-level recent performance |
| `teammate_delta` | Driver vs teammate relative feature |
| `reliability_score` | DNF/mechanical/constructor risk proxy |
| `penalty_risk` | Grid/race-control/news penalty flag |
| `weather_risk` | Rain/temperature/wind uncertainty proxy |
| `news_risk` | News-derived risk flag score |
| `ownership_pct` | Selection/ownership if available |
| `differential_score` | Inverse ownership adjusted for projection |

## Optimizer formulation

Decision variable:

```text
x_a = 1 if asset a is selected, otherwise 0
```

Constraints:

```text
sum(x_driver) = 5
sum(x_constructor) = 2
sum(price_a * x_a) <= cost_cap, except Limitless
locked assets: x_a = 1
banned assets: x_a = 0
chip constraints apply
```

Transfer variables can be derived from selected assets compared to current team.

Base objective:

```text
maximize expected_net_score =
  lineup_expected_points
- transfer_penalty_points
+ budget_growth_weight * expected_budget_delta
+ upside_weight * ceiling_points
- risk_weight * risk_score
+ differential_weight * differential_score
```

## Strategy modes

| Mode | Objective behavior |
|---|---|
| safe | Higher weight on floor/confidence, lower risk |
| balanced | Max expected net points with moderate risk penalty |
| aggressive | Higher ceiling/upside and differential weight |
| budget_builder | Weight expected price growth and future flexibility |
| differential | Weight low ownership and league gaps |
| chip_optimized | Compare all available chip scenarios |
| custom | User-defined weights |

Default weights:

```json
{
  "safe": {
    "expected": 0.60,
    "floor": 0.30,
    "ceiling": 0.05,
    "riskPenalty": 0.25,
    "budgetGrowth": 0.05,
    "differential": 0.00
  },
  "balanced": {
    "expected": 0.75,
    "floor": 0.10,
    "ceiling": 0.10,
    "riskPenalty": 0.12,
    "budgetGrowth": 0.08,
    "differential": 0.05
  },
  "aggressive": {
    "expected": 0.55,
    "floor": 0.00,
    "ceiling": 0.30,
    "riskPenalty": 0.03,
    "budgetGrowth": 0.05,
    "differential": 0.20
  },
  "budget_builder": {
    "expected": 0.50,
    "floor": 0.05,
    "ceiling": 0.05,
    "riskPenalty": 0.10,
    "budgetGrowth": 0.40,
    "differential": 0.00
  },
  "differential": {
    "expected": 0.55,
    "floor": 0.05,
    "ceiling": 0.20,
    "riskPenalty": 0.08,
    "budgetGrowth": 0.05,
    "differential": 0.30
  }
}
```

## Recommendation option output

Each option must include:

```json
{
  "optionId": "recopt_...",
  "rank": 1,
  "strategyMode": "balanced",
  "chipAction": "none",
  "transfers": [
    {"assetOutId": "asset_a", "assetInId": "asset_b", "reason": "Higher projected net points"}
  ],
  "expectedGrossPoints": 184.2,
  "transferPenaltyPoints": 0,
  "expectedNetPoints": 184.2,
  "budgetUsedMillions": 99.4,
  "budgetRemainingMillions": 0.6,
  "expectedBudgetDeltaMillions": 0.2,
  "riskScore": 0.34,
  "confidence": 0.72,
  "summary": "Use one free transfer and save chips.",
  "rationale": ["..."],
  "assumptions": ["..."],
  "warnings": ["..."]
}
```

## Brute-force fallback

Because the asset universe is small, brute-force is acceptable for many runs:

```python
for driver_combo in combinations(drivers, 5):
    for constructor_combo in combinations(constructors, 2):
        lineup = driver_combo + constructor_combo
        if not is_legal(lineup):
            continue
        score = score_lineup(lineup)
        collect(score)
```

Use pruning:

- filter inactive assets;
- apply locked/banned assets first;
- skip over-budget early;
- cap returned options to top N after stable sorting.

## Determinism

For the same input, the optimizer must produce the same ranked output.

Tie-breakers:

1. higher expected net points;
2. lower risk;
3. higher confidence;
4. more budget remaining;
5. fewer transfers;
6. lexicographic asset IDs.

## Backtesting

v1 must include a backtesting page or CLI command:

```bash
uv run raceweek backtest --season 2025 --strategy balanced
```

Backtest output:

- projected vs actual points;
- mean absolute error;
- strategy rank vs baseline;
- chip timing simulation;
- model calibration chart data.

## Test cases

Required unit tests:

- legal lineup with 5 drivers/2 constructors passes;
- duplicate asset fails;
- over-budget lineup fails;
- Limitless ignores budget for one event;
- Wildcard removes transfer penalty;
- standard extra transfers cost penalty;
- net-transfer counting ignores reorder;
- No Negative floors negative scores;
- Autopilot assigns boost to top actual/projection depending simulation mode;
- optimizer returns deterministic ordering;
- locked assets remain selected;
- banned assets are excluded;
- recommendation includes provenance IDs.


<!-- END docs/09_OPTIMIZER_PROJECTION_ENGINE.md -->


---

<!-- BEGIN docs/10_UI_UX_DESIGN_SYSTEM.md -->

# 10 — UI/UX and Design System

## Product feel

The app should feel like a modern strategy cockpit: sharp, data-dense, calm, and confident. It should not copy Formula 1 official visual identity.

Recommended visual direction:

- dark-first interface;
- neutral charcoal backgrounds;
- subtle grid/track-inspired geometry;
- high-contrast cards;
- clear status chips;
- one accent color chosen by project maintainers, not official F1 red;
- no official logos, team badges, driver photos, broadcast graphics, or proprietary typefaces.

## Information architecture

Primary navigation:

```text
Dashboard
Race Week
Optimizer
Market
My Teams
League
AI Strategist
Data Health
Settings
```

## Page requirements

### 1. Setup Wizard

Steps:

1. Welcome + unofficial disclaimer.
2. Choose local/demo/live mode.
3. Configure data sources.
4. Configure AI provider.
5. Import team or connect read-only token.
6. Validate data health.
7. Generate first recommendation.

Required states:

- no AI provider configured;
- local Ollama unavailable;
- fantasy connector unavailable;
- manual import invalid;
- data sync partially failed;
- success.

### 2. Dashboard

Sections:

- Next Race card.
- Team summary cards for up to three teams.
- Recommendation highlight.
- Budget/transfer/chip status.
- Data-health strip.
- News risk strip.
- Projection delta chart.

Dashboard must answer in five seconds of reading:

- What is the next event?
- Is my data fresh?
- What move is currently recommended?
- Is a chip recommended?
- What is the biggest risk?

### 3. Race Week

Sections:

- event timeline;
- sessions/results;
- weather observations;
- race-control and penalty feed;
- practice/quali/race summary;
- news and risk flags;
- “rerun projections” button.

### 4. Optimizer

Main components:

- strategy mode selector;
- team selector;
- lock/ban assets controls;
- chip scenario toggles;
- ranked recommendation cards;
- comparison drawer;
- explanation panel;
- export/copy action list.

Recommendation card fields:

- rank;
- title;
- transfer list;
- chip action;
- expected net points;
- transfer penalty;
- budget after move;
- risk/confidence;
- key rationale;
- warnings;
- assumptions;
- source snapshots.

### 5. Market

Table columns:

- asset;
- type;
- constructor/team;
- price;
- projected points;
- P10/P90;
- points per million;
- recent points;
- price trend;
- ownership;
- differential score;
- risk;
- tags.

Interactions:

- sort;
- filter;
- compare;
- add to locked/banned list;
- open asset details drawer.

### 6. My Teams

Shows:

- team snapshots;
- current lineup;
- budget;
- free transfers;
- chips;
- historical team changes;
- import/update button.

### 7. League

Shows:

- league table if available;
- user rank/gap;
- rival overlap;
- common assets;
- differential suggestions;
- catch-up strategy.

### 8. AI Strategist

Chat interface with:

- context chips for selected team/event;
- provider/model selector;
- prompt suggestions;
- cited recommendation IDs;
- tool-call transparency panel;
- stale-data warnings.

Suggested prompts:

- “What is my safest move this week?”
- “Should I use a chip?”
- “I am 80 points behind. What aggressive move makes sense?”
- “Compare the top two recommendations.”
- “What news changes the projections?”

### 9. Data Health

Table:

- source;
- status;
- last sync;
- freshness;
- last error;
- connector version;
- license/legal note;
- actions.

Actions:

- sync now;
- disable source;
- open docs;
- clear cache;
- inspect snapshots.

### 10. Settings

Sections:

- AI providers;
- data sources;
- ruleset;
- projection weights;
- privacy;
- import/export;
- about/legal.

## Component system

Required reusable components:

- `StatusBadge`
- `DataFreshnessBadge`
- `RiskMeter`
- `ConfidenceMeter`
- `MetricCard`
- `RecommendationCard`
- `TransferPill`
- `ChipBadge`
- `AssetAvatarPlaceholder`
- `AssetComparisonDrawer`
- `SourceSnapshotLink`
- `ProviderConfigForm`
- `EmptyState`
- `ErrorState`
- `LoadingSkeleton`

## Responsive behavior

- Desktop: side nav and two/three-column dashboard.
- Tablet: collapsible nav, two-column cards.
- Mobile: bottom nav or top menu, single-column cards, tables become cards/drawers.

## Accessibility

Minimum requirements:

- semantic headings;
- keyboard navigation for all controls;
- visible focus states;
- color is never the only status indicator;
- labels for all inputs;
- chart data available in tables or summaries;
- contrast meets WCAG AA.

## Empty/error states

Every page must have useful states:

- no team imported;
- no upcoming race found;
- no AI provider configured;
- connector disabled;
- stale data;
- optimizer cannot find legal lineup;
- projections missing;
- provider request failed.

Example empty state:

```text
No fantasy team imported yet.
Import your team manually or configure a read-only fantasy connector. You can still explore demo mode.
```

## Copywriting style

Use direct, helpful language:

- “Recommended move” instead of “AI insight”.
- “Data is stale” instead of “Something went wrong”.
- “Manual action required” instead of “Transfer submitted”.
- “Confidence” and “Risk” should always be accompanied by explanation.

## Legal UI text

Footer/about page must include:

```text
RaceWeek Strategist is an unofficial fan-made fantasy analytics tool. It is not affiliated with, endorsed by, or sponsored by Formula 1, Formula One Management, or any team/constructor. Users are responsible for complying with the terms of the services they connect.
```


<!-- END docs/10_UI_UX_DESIGN_SYSTEM.md -->


---

<!-- BEGIN docs/11_SECURITY_PRIVACY_LEGAL.md -->

# 11 — Security, Privacy, and Legal Guardrails

## Product posture

RaceWeek Strategist is an unofficial fan-made analytics tool. It must not imply official status or use protected branding as product identity.

## Legal constraints to design around

### Branding

Do not use:

- official Formula 1 logos;
- official F1 word marks as product branding;
- official typefaces;
- official team logos;
- official driver images;
- broadcast graphics;
- official app screenshots as marketing assets.

Allowed posture:

- plain-text editorial references where necessary to explain compatibility;
- prominent unofficial disclaimer;
- independent project name and visual identity.

### Data and content

Do not:

- scrape or redistribute substantial official timing/results/statistics content where not licensed;
- store full copyrighted articles by default;
- bypass paywalls;
- use Formula 1-owned content to train, develop, or operate AI models unless licensed;
- bundle proprietary data in test fixtures.

Do:

- rely on documented/open/community APIs where permitted;
- store provenance and license notes;
- support manual user import;
- store short metadata and summaries for news, not article mirrors;
- use synthetic/demo fixtures in repository.

### Fantasy account actions

v1 must be read-only with respect to the official fantasy account. The app can recommend moves, but the user executes them manually.

Disallowed:

- automated login with username/password;
- auto-submitting transfers;
- bypassing anti-bot protections;
- scraping user account data without explicit user action.

## Privacy

Default privacy stance:

- local-first;
- no telemetry by default;
- no hosted account required;
- no secrets in browser;
- no secrets in logs;
- no AI prompts containing unnecessary personal data.

## Secrets management

Supported local secret sources:

1. `.env` file excluded by `.gitignore`;
2. environment variables;
3. local encrypted secret store later, if implemented;
4. Docker secrets for advanced deployment.

Never store:

- provider API keys in database plaintext;
- fantasy bearer tokens in raw snapshots;
- authorization headers;
- cookies;
- passwords.

Redaction patterns:

- `sk-...` style API keys;
- bearer tokens;
- session cookies;
- OAuth tokens;
- provider-specific key prefixes;
- long high-entropy strings in logs.

## AI prompt privacy

Only send the minimum relevant data to AI providers.

Allowed in prompts:

- selected team assets;
- budget;
- transfer count;
- recommendation options;
- risk summaries;
- data freshness status.

Avoid unless explicitly needed:

- user email;
- user global ID;
- league member names;
- raw tokens;
- full news article text;
- raw external API payloads.

## Supply-chain security

- Pin direct dependencies.
- Commit lockfiles.
- Run dependency audit in CI.
- Use secret scanning.
- Pin GitHub Actions by SHA.
- Avoid unnecessary transitive-heavy AI abstraction libraries.
- Review AI/agent dependencies with extra scrutiny.
- Never install known-compromised versions.

## Threat model

### Threat: Provider API key leakage

Mitigations:

- server-side provider calls only;
- env var references instead of stored key values;
- log redaction;
- prompt redaction;
- no frontend exposure.

### Threat: Fantasy token leakage

Mitigations:

- local-only storage;
- never store in raw snapshot;
- no token in query strings;
- optional manual import;
- user can clear token.

### Threat: Malicious dependency

Mitigations:

- lockfiles;
- package provenance review;
- dependency audit;
- minimal dependencies;
- CI install from lockfile only;
- renovate/dependabot with human review.

### Threat: AI hallucinated recommendation

Mitigations:

- deterministic recommendation IDs;
- AI must reference optimizer outputs;
- post-response validation;
- tests/evals;
- show data freshness.

### Threat: Upstream API breaking change

Mitigations:

- connector contract tests;
- source health UI;
- manual import fallback;
- endpoint map configuration;
- graceful degradation.

## Security headers for hosted mode

If hosted behind reverse proxy:

- HTTPS only;
- HSTS;
- CSP;
- `X-Content-Type-Options: nosniff`;
- `Referrer-Policy: strict-origin-when-cross-origin`;
- CSRF protection if cookies are used;
- authenticated access.

## Data deletion

Settings must include:

- clear provider config;
- clear fantasy token/session;
- delete local database;
- export user data;
- delete conversations;
- clear raw snapshots.

## Disclaimer text

Use this in README, UI footer, and About page:

```text
RaceWeek Strategist is an unofficial fan-made fantasy analytics tool. It is not affiliated with, endorsed by, or sponsored by Formula 1, Formula One Management, or any team/constructor. Users are responsible for complying with the terms of the services they connect.
```

## Maintainer checklist before public release

- No official logos/assets in repository.
- No real user data in fixtures.
- No secrets in git history.
- No unlicensed full article content.
- README contains disclaimer.
- Connector docs explain optional/user-responsibility nature.
- Terms/legal docs reviewed by maintainer.
- Security policy exists.


<!-- END docs/11_SECURITY_PRIVACY_LEGAL.md -->


---

<!-- BEGIN docs/12_TESTING_TDD_QA.md -->

# 12 — Testing, TDD, and QA Strategy

## Testing philosophy

The project is a strategy engine with a polished UI. Bugs can create bad decisions, so domain correctness matters more than superficial coverage.

Use test-driven development for:

- rules engine;
- transfer counting;
- chip simulation;
- optimizer constraints;
- projection feature calculations;
- provider/tool guardrails;
- connector normalization.

## Test pyramid

```text
                 E2E tests
              Playwright UI flows
          ─────────────────────────
          API integration tests
       FastAPI + temporary DuckDB
   ───────────────────────────────────
   Domain and connector unit tests
 Rules • optimizer • projections • schemas
```

## Coverage targets

| Area | Minimum |
|---|---:|
| Rules engine | 95% |
| Optimizer | 95% |
| Projection feature engine | 90% |
| Connectors normalization | 85% |
| API routes | 80% |
| Web business logic | 75% |
| UI snapshots/visual checks | Best effort |

Coverage alone is not enough. Edge-case tests are required.

## Required backend test suites

### Rules engine tests

- legal lineup passes;
- too few drivers fails;
- too many constructors fails;
- duplicate assets fail;
- over-budget lineup fails;
- missing price fails with clear error;
- transfer count ignores order;
- transfer count equals net asset changes;
- extra transfers apply penalty;
- Wildcard zeroes transfer penalty;
- Limitless ignores budget cap for event;
- No Negative floors negative scores;
- 3x boost applies configured multiplier;
- Autopilot assigns boost according to configured simulation;
- Final Fix allows only one late driver change.

### Optimizer tests

- returns only legal lineups;
- honors locked assets;
- honors banned assets;
- does not exceed budget except Limitless;
- ranks by deterministic tie-breakers;
- includes transfer penalty in net score;
- returns no options with useful error when constraints impossible;
- strategy modes change ranking as expected;
- option output includes rationale, assumptions, and warnings.

### Projection tests

- rolling averages calculate correctly;
- missing data lowers confidence;
- stale source lowers confidence;
- risk flags increase risk score;
- contribution breakdown sums to expected score within tolerance;
- price delta model handles missing history;
- model version is stored.

### Connector tests

Use `respx` for HTTP mocking.

- happy path normalizes expected fixture;
- non-200 response creates degraded/error status;
- invalid JSON handled;
- rate-limit headers handled;
- secrets redacted;
- raw snapshot created;
- schema change produces warning instead of silent corruption.

### API tests

- OpenAPI schema validates;
- endpoints return expected status codes;
- invalid request bodies return typed error envelope;
- recommendations create run records;
- data-source statuses are returned;
- chat endpoint works with fake provider.

### AI/provider tests

Do not call live providers in CI.

Use fake provider fixtures to test:

- provider registry;
- provider config validation;
- tool-call orchestration;
- no secret leakage;
- no auto-transfer behavior;
- stale data warning;
- deterministic fallback template when provider fails.

## Required frontend test suites

### Unit/component tests

- `RecommendationCard` renders all metrics;
- `RiskMeter` handles low/medium/high;
- `DataFreshnessBadge` handles stale/degraded/error;
- setup wizard validates provider fields;
- market filters and sort state;
- locked/banned asset controls.

### Playwright E2E flows

1. Demo first run.
   - launch app;
   - complete setup in demo mode;
   - see dashboard;
   - open optimizer;
   - generate recommendation;
   - open AI Strategist with fake provider.

2. Manual import.
   - import fixture team;
   - import market;
   - run projections;
   - run optimizer;
   - compare two recommendation cards.

3. Data-source failure.
   - simulate failed connector;
   - show data health degraded;
   - optimizer still works with last snapshot or manual data.

4. Provider failure.
   - configure fake provider failure;
   - chat shows fallback/error state;
   - deterministic recommendation remains visible.

## Fixtures

Fixtures must be synthetic or license-safe. Do not commit real official data unless clearly permitted.

Required fixture files:

```text
packages/fixtures/
  fantasy_market_demo.json
  fantasy_team_demo.json
  fantasy_scores_demo.csv
  race_calendar_demo.json
  openf1_session_demo.json
  news_demo.json
  league_demo.json
```

Use fictional names in fixtures by default:

- Driver Alpha;
- Driver Bravo;
- Constructor One;
- Constructor Two.

This avoids redistribution of proprietary current data.

## Golden tests

Recommendation output should have golden tests:

```text
tests/golden/balanced_recommendation.json
tests/golden/chip_limitless_recommendation.json
tests/golden/differential_recommendation.json
```

Golden tests must ignore volatile fields:

- generated timestamp;
- run ID;
- snapshot ID if generated.

## Property-style tests

Even without adding a property-testing dependency, create randomized tests for:

- lineup legality;
- transfer counting symmetry;
- optimizer never returns banned assets;
- net score never ignores transfer penalty;
- budget cap always enforced in non-Limitless modes.

## QA checklist before release

- Fresh clone setup passes.
- Demo mode works offline except package install.
- Manual import works.
- Fantasy connector disabled state works.
- OpenF1/Jolpica connector tests pass with fixtures.
- AI provider fake tests pass.
- Ollama local config path documented.
- No official assets/logos in repo.
- No secrets in repo or logs.
- `make check` passes.
- Playwright E2E passes.
- README and disclaimer present.
- License and security policy present.

## CI pipeline

Required jobs:

```text
lint-python
lint-web
typecheck-python
typecheck-web
test-python
test-web
e2e-demo
openapi-validate
schema-validate
secret-scan
dependency-audit
```

CI must run with fixture/demo data only. Live connector tests may run in a separate scheduled workflow with maintainer-provided secrets, but they must not block normal contributor PRs.

## Definition of done

A pull request is not done until:

- tests are included;
- docs are updated;
- fixtures are safe;
- no secrets/log leaks;
- UI has error/loading/empty state;
- source provenance is recorded when data is involved;
- accessibility basics are considered;
- `make check` passes locally and in CI.


<!-- END docs/12_TESTING_TDD_QA.md -->


---

<!-- BEGIN docs/13_DEVOPS_MONOREPO_DEPLOYMENT.md -->

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
6. optionally seed demo data.

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
- demo mode verified;
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


<!-- END docs/13_DEVOPS_MONOREPO_DEPLOYMENT.md -->


---

<!-- BEGIN docs/14_IMPLEMENTATION_PLAN.md -->

# 14 — Implementation Plan

This plan sequences v1 delivery. It does not defer features out of v1.

## Milestone 0 — Repository scaffold

Deliverables:

- pnpm workspace;
- FastAPI app scaffold;
- Next.js app scaffold;
- Docker Compose;
- Makefile;
- CI skeleton;
- README/disclaimer;
- license/security/contributing docs.

Acceptance:

- `make setup` works;
- `make dev` starts web/API;
- `/health` returns ok;
- web shell loads.

## Milestone 1 — Contracts and database

Deliverables:

- OpenAPI integrated;
- Pydantic models;
- Zod/TS types;
- DuckDB migrations;
- source snapshot repository;
- demo fixtures;
- seed-demo command.

Acceptance:

- migrations apply cleanly;
- fixtures load;
- schema validation tests pass.

## Milestone 2 — Rules engine

Deliverables:

- versioned ruleset model;
- lineup validator;
- budget validator;
- transfer counter;
- chip simulator;
- exhaustive unit tests.

Acceptance:

- rules engine coverage >=95%;
- all required chip/transfer tests pass.

## Milestone 3 — Data connectors

Deliverables:

- manual import connector;
- fantasy read-only connector;
- OpenF1 connector;
- Jolpica connector;
- FastF1 adapter;
- RSS/news connector;
- data-health API/UI.

Acceptance:

- connector tests use fixtures/mocked HTTP;
- broken connector creates degraded status;
- no secrets in snapshots/logs.

## Milestone 4 — Feature and projection engine

Deliverables:

- feature computation jobs;
- transparent weighted model;
- projection run storage;
- contribution breakdown;
- backtest CLI/page.

Acceptance:

- projections produce expected fixture outputs;
- stale data lowers confidence;
- backtest command runs on demo fixtures.

## Milestone 5 — Optimizer

Deliverables:

- brute-force optimizer;
- OR-Tools optimizer path;
- strategy modes;
- chip scenario comparison;
- recommendation persistence;
- optimizer API.

Acceptance:

- optimizer returns legal deterministic results;
- recommendation cards have complete data;
- no impossible lineups returned.

## Milestone 6 — Polished UI

Deliverables:

- setup wizard;
- dashboard;
- race-week page;
- market table;
- optimizer page;
- my teams page;
- league page;
- data-health page;
- settings page;
- responsive styling and accessibility.

Acceptance:

- Playwright demo flow passes;
- all pages have loading/empty/error states;
- UI disclaimer present;
- no official assets/logos.

## Milestone 7 — AI provider and agent layer

Deliverables:

- provider registry;
- OpenAI adapter;
- Anthropic adapter;
- Gemini adapter;
- Ollama adapter;
- OpenRouter/Groq/xAI/custom OpenAI-compatible adapter;
- Mistral adapter;
- fake provider for tests;
- tool orchestrator;
- strategy chat UI;
- prompt templates/evals.

Acceptance:

- fake provider tests pass;
- provider failure fallback works;
- no AI response can auto-transfer;
- AI cites recommendation/data IDs.

## Milestone 8 — League strategy

Deliverables:

- league import;
- rival overlap analysis;
- differential scoring;
- catch-up strategy mode;
- league UI page;
- AI league prompts.

Acceptance:

- demo league analysis works;
- optimizer can use differential weights;
- missing league fields degrade gracefully.

## Milestone 9 — QA, docs, release

Deliverables:

- complete README;
- setup docs;
- connector docs;
- provider docs;
- contribution docs;
- release checklist;
- test coverage reports;
- dependency audit;
- v1.0.0 tag.

Acceptance:

- fresh clone demo verified;
- `make check` passes;
- docs reviewed;
- no secrets or protected assets;
- release notes published.

## Build order inside each milestone

1. Write tests.
2. Add typed models/contracts.
3. Implement core/domain logic.
4. Implement storage/repository.
5. Implement API.
6. Implement UI.
7. Update docs.
8. Run `make check`.

## Do not cut these corners

- Do not fake fantasy prices or rules in live mode.
- Do not let AI produce transfer advice without optimizer output.
- Do not use official images/logos for polish.
- Do not leave provider errors as unhandled exceptions.
- Do not skip data provenance.
- Do not ship without demo mode.


<!-- END docs/14_IMPLEMENTATION_PLAN.md -->


---

<!-- BEGIN docs/15_OBSERVABILITY_OPERATIONS.md -->

# 15 — Observability and Operations

## Operational goal

Users should always know whether recommendations are based on fresh, complete data or stale/degraded data.

## Observability surfaces

### Data Health page

Shows every source:

- status;
- last successful sync;
- last attempted sync;
- freshness;
- rate-limit state;
- latest error;
- connector version;
- user action.

### Recommendation provenance panel

Every recommendation option has a “Why this?” or “Sources” panel showing:

- recommendation run ID;
- projection run ID;
- ruleset version;
- optimizer version;
- source snapshot IDs;
- data freshness;
- assumptions;
- warnings.

### Logs

Use structured JSON logs in API:

```json
{
  "level": "INFO",
  "event": "optimizer.run.completed",
  "requestId": "req_...",
  "recommendationRunId": "recrun_...",
  "durationMs": 83
}
```

## Log redaction

Implement a central redactor for:

- authorization headers;
- cookies;
- API keys;
- bearer tokens;
- high-entropy strings;
- provider request bodies when configured.

## Connector run records

Each sync should record:

- sync ID;
- source;
- start/end time;
- status;
- rows fetched;
- rows normalized;
- snapshot IDs;
- error message;
- retry count.

This can be implemented as a table later, but v1 must at least expose source status from `source_snapshots` and logs.

## Health checks

`GET /health` returns API process health.

`GET /api/v1/app/status` returns:

- version;
- setup status;
- DB status;
- current event;
- required connector availability.

Do not make `/health` fail because an external API is down. External source health belongs in data-source status.

## Local troubleshooting UX

Settings/Data Health should include actions:

- retry sync;
- force refresh;
- disable source;
- switch to manual import;
- clear cache;
- open logs location;
- export diagnostics without secrets.

## Diagnostics export

Diagnostics export must include:

- app version;
- OS/container metadata if available;
- connector statuses;
- last 100 redacted logs;
- OpenAPI version;
- schema versions;
- dependency versions;
- no secrets;
- no raw tokens;
- no raw full news articles.


<!-- END docs/15_OBSERVABILITY_OPERATIONS.md -->


---

<!-- BEGIN docs/16_CONTRIBUTING_OPEN_SOURCE.md -->

# 16 — Contributing and Open-Source Governance

## License

Recommended v1 license: Apache-2.0.

Reasoning:

- permissive and familiar;
- friendly to contributors and downstream users;
- includes patent grant;
- avoids friction for a new community project.

If maintainers want to prevent closed hosted forks, evaluate AGPL-3.0 before first public release. Do not change license casually after accepting contributions.

## Contribution areas

- data connectors;
- projection models;
- optimizer strategies;
- UI components;
- AI provider adapters;
- docs;
- tests/fixtures;
- accessibility;
- localization.

## Pull request rules

Every PR must:

- describe the change;
- include tests;
- update docs if behavior changes;
- avoid official/proprietary assets;
- avoid secrets and real user data;
- pass CI.

## Connector contribution rules

New connectors must include:

- source license/terms note;
- rate-limit behavior;
- typed raw/normalized models;
- fixture tests;
- data-health status;
- fallback behavior;
- no secrets in logs.

## Projection model contribution rules

New projection models must include:

- model name/version;
- input features;
- output schema;
- backtest method;
- explainability payload;
- tests;
- configuration defaults.

## AI provider contribution rules

New providers must include:

- provider config schema;
- fake provider tests;
- error handling;
- streaming behavior if supported;
- tool-call support if available;
- no dependency bloat unless justified.

## Code of conduct

Adopt Contributor Covenant or similar. Keep community friendly and clear that the project is unofficial.

## Security reporting

Create `SECURITY.md` with:

- supported versions;
- private vulnerability report method;
- expected response timeline;
- secret leakage procedures;
- dependency compromise procedures.

## Documentation expectations

Every user-facing feature needs:

- short README mention;
- setup/config docs;
- troubleshooting notes;
- screenshot later if project assets are safe.


<!-- END docs/16_CONTRIBUTING_OPEN_SOURCE.md -->


---

<!-- BEGIN docs/17_PROMPT_TEMPLATES_EVALS.md -->

# 17 — Prompt Templates and AI Evals

## System prompt

Canonical prompt lives at `examples/prompts/agent-system-prompt.md`.

## Prompt design rules

- Keep rules and data as structured context.
- Do not ask the model to calculate legal lineups.
- Ask the model to explain already-computed recommendations.
- Require the model to state uncertainty and stale data.
- Require the model to refuse automatic transfer execution.

## Recommendation explanation prompt

Template:

```text
You are explaining a fantasy motorsport recommendation from a deterministic optimizer.
Do not invent drivers, prices, scores, or rules.
Use only the provided recommendation payload and data-health payload.

User question:
{{user_question}}

Team snapshot:
{{team_snapshot_json}}

Recommendation run:
{{recommendation_run_json}}

Data health:
{{data_health_json}}

Respond with:
1. Recommendation
2. Expected impact
3. Why
4. Risks
5. What would change this
6. Data freshness
```

## Chip explanation prompt

```text
Compare the no-chip scenario and chip scenarios below.
Explain whether the user should use a chip now or save it.
Do not claim certainty. Mention opportunity cost.

No-chip option:
{{no_chip_option}}

Chip options:
{{chip_options}}

Remaining season context:
{{season_context}}
```

## News impact prompt

```text
Summarize how the following news items may affect the user's fantasy strategy.
Only use the supplied news metadata and summaries.
Do not quote long article text.
Map risk flags to affected assets.

News:
{{news_items_json}}

Current recommendations:
{{recommendation_options_json}}
```

## Eval fixtures

Create fixtures:

```text
examples/prompts/evals/
  transfer_safe.json
  transfer_aggressive.json
  chip_limitless_save.json
  chip_no_negative_use.json
  stale_data_warning.json
  provider_failure_fallback.json
  league_chase.json
  auto_transfer_refusal.json
```

## Eval assertions

For each model response, assert:

- does not say it submitted a transfer;
- contains recommendation ID for transfer advice;
- mentions stale/degraded data if present;
- does not invent asset names not in payload;
- does not expose secrets;
- includes risk or uncertainty;
- stays under configured token limit;
- follows requested format.

## Deterministic fallback explanation

When no provider is configured or provider fails, generate template-based explanations:

```text
Recommended move: {summary}
Expected net impact: {expectedNetPoints} projected points after {transferPenaltyPoints} transfer penalty.
Confidence: {confidence}
Main reasons: {topRationale}
Risks: {warnings}
Data freshness: {dataHealthSummary}
```

The product must remain useful without AI.


<!-- END docs/17_PROMPT_TEMPLATES_EVALS.md -->


---

<!-- BEGIN docs/18_ADR_INDEX.md -->

# 18 — Architecture Decision Record Index

| ADR | Decision |
|---|---|
| ADR-0001 | Use Next.js + FastAPI monorepo |
| ADR-0002 | Use DuckDB for local-first analytics store |
| ADR-0003 | Use self-authored AI provider adapters instead of LiteLLM as core dependency |
| ADR-0004 | Deterministic optimizer is source of truth |
| ADR-0005 | Fantasy connector is read-only with manual import fallback |
| ADR-0006 | OpenF1 + Jolpica + FastF1 for race data |
| ADR-0007 | Avoid official Formula 1 branding and protected assets |
| ADR-0008 | Use Apache-2.0 license for v1 |
| ADR-0009 | OpenAPI + JSON Schema as implementation contracts |


<!-- END docs/18_ADR_INDEX.md -->


---

<!-- BEGIN docs/19_REFERENCES.md -->

# 19 — References and Source Notes

This package was prepared with information available on June 5, 2026. Verify source availability during implementation.

## Fantasy game/rules references

- Formula 1 official fantasy 2026 article: documents current high-level game structure including five drivers, two constructors, $100m cost cap, three teams, two free transfers, net-transfer counting changes, Sprint DNF change, and chip examples.
- Fantasy Formula 1 “How to play” and “Game rules” pages: document transfer allowance and extra-transfer penalties.

## Formula 1 IP/legal references

- Formula 1 brand/IP guidelines: use for unofficial disclaimer, no logo usage, careful word-mark use, data/media restrictions, and AI-related restrictions.

## Fantasy API references

- dltHub F1 Fantasy REST API context: documents base URL, token approach, and example endpoints.
- Community F1 Fantasy API repositories/Postman collections: useful for connector discovery, but treat as unofficial and brittle.

## Race data references

- OpenF1 API documentation and homepage: endpoints for meetings, sessions, drivers, laps, pit, race control, weather, etc.; free historical data and rate limits; unofficial/non-commercial posture.
- Jolpica API: Ergast-compatible endpoint for F1 schedules/results/standings.
- FastF1 documentation/PyPI: Python package for schedules, results, timing, telemetry, caching, and Jolpica integration.

## AI provider references

- OpenAI platform docs: Responses API, models, tools.
- Anthropic docs: Messages API, tools, SDKs.
- Google GenAI docs: official Python SDK.
- Ollama docs: local API and OpenAI-compatible endpoints.
- OpenRouter docs: OpenAI-compatible chat API.
- Groq docs: OpenAI-compatible API.
- xAI docs: OpenAI/Anthropic SDK-compatible API.
- Mistral docs: official SDK and API docs.

## Dependency/security references

- PyPI/npm package pages for version pins.
- LiteLLM security update and public security reporting for AI-package supply-chain risk.
- Mistral security advisory for compromised SDK release context.

## Implementation note

Do not copy facts from these sources into runtime claims without storing source provenance. External rules and APIs can change.


<!-- END docs/19_REFERENCES.md -->


---

<!-- BEGIN docs/20_IMPLEMENTATION_CHECKLIST.md -->

# 20 — v1 Acceptance Checklist

Use this as the release gate for v1.0.0.

## Product

- [ ] Setup wizard works in demo mode.
- [ ] Setup wizard works with manual team import.
- [ ] Dashboard shows next event, team state, recommendation, and data health.
- [ ] Market table supports sorting/filtering/comparison.
- [ ] Optimizer returns safe/balanced/aggressive/budget/differential/chip modes.
- [ ] Race Week page shows sessions, weather, race-control, news, and stale-data states.
- [ ] AI Strategist works with fake provider and at least one real configured provider.
- [ ] League analysis works with imported demo league data.
- [ ] Settings page manages providers, data sources, rules, privacy, import/export.

## Data

- [ ] Manual import validates JSON and CSV.
- [ ] Fantasy connector is optional and read-only.
- [ ] OpenF1 connector works with fixture/mocked tests.
- [ ] Jolpica connector works with fixture/mocked tests.
- [ ] FastF1 adapter works with cache path.
- [ ] News connector stores metadata/summary only.
- [ ] Source snapshots are recorded.
- [ ] Data health is visible in UI.

## Rules/optimizer

- [ ] 5-driver/2-constructor constraints tested.
- [ ] Budget cap tested.
- [ ] Transfer penalties tested.
- [ ] Net-transfer counting tested.
- [ ] All chips tested.
- [ ] Optimizer deterministic ordering tested.
- [ ] Recommendations include provenance.

## AI

- [ ] Provider registry supports required providers.
- [ ] No provider key is exposed to browser.
- [ ] Fake provider test suite passes.
- [ ] AI refuses auto-transfer requests.
- [ ] AI references recommendation IDs for transfer advice.
- [ ] Fallback template works without AI.

## UI/UX

- [ ] Responsive desktop/tablet/mobile.
- [ ] Dark mode.
- [ ] Empty/loading/error states.
- [ ] Accessibility basics.
- [ ] No official logos/assets.
- [ ] Unofficial disclaimer in footer/about.

## Engineering

- [ ] `make setup` works from fresh clone.
- [ ] `make dev` starts app.
- [ ] `make check` passes.
- [ ] CI runs lint/typecheck/tests/e2e.
- [ ] Lockfiles committed.
- [ ] Dependency audit reviewed.
- [ ] Docs updated.
- [ ] Security policy present.
- [ ] License selected.


<!-- END docs/20_IMPLEMENTATION_CHECKLIST.md -->


---

<!-- BEGIN docs/adrs/ADR-0001-nextjs-fastapi-monorepo.md -->

# ADR-0001 — Use Next.js + FastAPI Monorepo

## Status

Accepted.

## Context

The product needs a polished dashboard UI and a Python-heavy analytics backend for connectors, projections, optimization, and AI provider SDKs.

## Decision

Use a pnpm monorepo with:

- `apps/web`: Next.js, React, TypeScript;
- `apps/api`: FastAPI, Python;
- `packages/contracts`: shared OpenAPI/JSON schemas;
- `packages/fixtures`: demo/test data.

## Consequences

Positive:

- best tool for each layer;
- easier data science integration;
- clean API boundary;
- good contributor ergonomics.

Negative:

- two runtimes;
- more setup complexity;
- must keep contracts synchronized.

Mitigation:

- Docker Compose;
- Makefile;
- generated API types;
- OpenAPI as source of truth.


<!-- END docs/adrs/ADR-0001-nextjs-fastapi-monorepo.md -->


---

<!-- BEGIN docs/adrs/ADR-0002-duckdb-local-first.md -->

# ADR-0002 — Use DuckDB for Local-First Analytics Store

## Status

Accepted.

## Context

The project should be open-source, easy to run locally, and analytics-heavy. Users should not need to administer Postgres to try it.

## Decision

Use DuckDB as the default database. Store it at `./data/raceweek.duckdb`.

## Consequences

Positive:

- zero-admin local setup;
- excellent analytical SQL;
- easy snapshot/export;
- simple Docker volume.

Negative:

- not ideal for multi-user hosted writes;
- migrations must be managed carefully;
- fewer auth/multi-tenant primitives than Postgres.

Mitigation:

- keep storage behind repository interfaces;
- hosted mode can later add Postgres adapter;
- use source snapshots and typed repositories.


<!-- END docs/adrs/ADR-0002-duckdb-local-first.md -->


---

<!-- BEGIN docs/adrs/ADR-0003-ai-provider-adapters.md -->

# ADR-0003 — Use Self-Authored AI Provider Adapters

## Status

Accepted.

## Context

The project must support many providers: OpenAI, Anthropic, Gemini, Ollama, OpenRouter, Groq, xAI, Mistral, and custom OpenAI-compatible endpoints. All-in-one AI routing dependencies are convenient but increase supply-chain and abstraction risk.

## Decision

Implement a small provider adapter interface directly. Use official SDKs where appropriate and OpenAI-compatible clients for compatible providers.

LiteLLM is not a core runtime dependency in v1.

## Consequences

Positive:

- lower dependency risk;
- easier to audit;
- precise provider behavior;
- simpler secret handling.

Negative:

- more adapter code;
- provider differences must be handled explicitly.

Mitigation:

- keep interface small;
- fake provider for tests;
- provider-specific tests;
- optional gateway integration can be added later.


<!-- END docs/adrs/ADR-0003-ai-provider-adapters.md -->


---

<!-- BEGIN docs/adrs/ADR-0004-deterministic-optimizer-source-of-truth.md -->

# ADR-0004 — Deterministic Optimizer Is Source of Truth

## Status

Accepted.

## Context

LLMs can explain and synthesize, but they are not reliable calculators for fantasy rules, budgets, transfer penalties, and lineup constraints.

## Decision

Use deterministic rules, projection, and optimization services as the source of truth. The LLM can call tools and explain outputs but cannot create unsourced transfer recommendations.

## Consequences

Positive:

- reproducible recommendations;
- testable logic;
- fewer hallucinations;
- user trust.

Negative:

- more up-front engineering;
- model output may feel less magical.

Mitigation:

- polished AI explanations;
- recommendation cards with rationale;
- strategy modes and what-if tools.


<!-- END docs/adrs/ADR-0004-deterministic-optimizer-source-of-truth.md -->


---

<!-- BEGIN docs/adrs/ADR-0005-fantasy-read-only-manual-fallback.md -->

# ADR-0005 — Fantasy Connector Is Read-Only with Manual Import Fallback

## Status

Accepted.

## Context

Fantasy APIs and terms can change. Automated login/transfer execution creates legal, security, and account-risk concerns.

## Decision

v1 supports manual import and optional read-only token/session-based connector. It does not store passwords and does not auto-submit transfers.

## Consequences

Positive:

- safer legal posture;
- lower account risk;
- product still works when connector breaks;
- easier open-source launch.

Negative:

- less seamless than full automation;
- users may need to manually import/update.

Mitigation:

- make manual import polished;
- clear instructions;
- data-health warnings;
- optional token connector for advanced users.


<!-- END docs/adrs/ADR-0005-fantasy-read-only-manual-fallback.md -->


---

<!-- BEGIN docs/adrs/ADR-0006-race-data-sources.md -->

# ADR-0006 — Use OpenF1 + Jolpica + FastF1 for Race Data

## Status

Accepted.

## Context

The product needs session/race context, historical results, weather, race control, pit stops, and schedule data.

## Decision

Use:

- OpenF1 for modern session/weather/race-control/pit data;
- Jolpica for Ergast-compatible schedules/results/standings;
- FastF1 for Python data access, caching, and feature engineering.

## Consequences

Positive:

- complementary sources;
- open/community-friendly;
- good Python integration;
- historical and modern session coverage.

Negative:

- source licenses and limits differ;
- fields may not align perfectly;
- live data may require paid/limited access.

Mitigation:

- connector provenance;
- cache and rate limits;
- source-health UI;
- normalization tests.


<!-- END docs/adrs/ADR-0006-race-data-sources.md -->


---

<!-- BEGIN docs/adrs/ADR-0007-avoid-official-branding.md -->

# ADR-0007 — Avoid Official Formula 1 Branding and Protected Assets

## Status

Accepted.

## Context

Formula 1 brand/IP guidelines restrict logos, marks, official content, and data/media usage. The project is open-source and unofficial.

## Decision

Use an independent name and visual identity. Do not include official logos, team logos, driver photos, broadcast graphics, proprietary typefaces, or official media in the repository or UI.

## Consequences

Positive:

- lower legal risk;
- clearer unofficial positioning;
- easier open-source distribution.

Negative:

- less immediate visual association;
- UI must create its own polish.

Mitigation:

- use motorsport-inspired but original design;
- clear compatibility wording;
- prominent disclaimer.


<!-- END docs/adrs/ADR-0007-avoid-official-branding.md -->


---

<!-- BEGIN docs/adrs/ADR-0008-apache-license.md -->

# ADR-0008 — Use Apache-2.0 License for v1

## Status

Accepted.

## Context

The project wants open-source adoption, integrations, and community contributions.

## Decision

Use Apache-2.0 for v1 unless maintainers decide before public launch that AGPL-3.0 better matches project goals.

## Consequences

Positive:

- permissive;
- familiar;
- includes patent grant;
- easier for contributors and downstream users.

Negative:

- hosted closed-source forks are possible.

Mitigation:

- decide before first public release if this tradeoff is acceptable;
- build strong community and governance.


<!-- END docs/adrs/ADR-0008-apache-license.md -->


---

<!-- BEGIN docs/adrs/ADR-0009-openapi-jsonschema-contracts.md -->

# ADR-0009 — Use OpenAPI and JSON Schema as Contracts

## Status

Accepted.

## Context

The implementation agent needs clear contracts to avoid hallucinating shapes. The web and API need shared types.

## Decision

Use OpenAPI 3.1 for HTTP API and JSON Schema 2020-12 for important domain payloads. Generate client/server types where useful.

## Consequences

Positive:

- fewer mismatches;
- better docs;
- testable contracts;
- easier contributor onboarding.

Negative:

- schemas need maintenance;
- generation tooling adds complexity.

Mitigation:

- schemas live in repository;
- CI validates OpenAPI and JSON schemas;
- update schemas as part of feature PRs.


<!-- END docs/adrs/ADR-0009-openapi-jsonschema-contracts.md -->
