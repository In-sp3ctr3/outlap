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
