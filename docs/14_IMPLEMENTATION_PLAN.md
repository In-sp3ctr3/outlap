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
- license-safe fixtures for tests;
- seed-demo command for explicit fixture/backtest workflows.

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

- fresh clone real-data empty state verified;
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
- Do not ship the primary app with demo/dummy fallback enabled.
