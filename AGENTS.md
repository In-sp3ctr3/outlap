# Implementation Agent Instructions

You are implementing Outlap v1.

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

## Repository operating standards

- Treat Phase 0 repository hygiene as part of the product, not as optional polish.
- Keep commits small, human-readable, and reviewable. Use concise Conventional Commit messages.
- Do not include tool branding, prompt transcripts, generated-code disclaimers, or co-author trailers in commits or project docs.
- Update `CHANGELOG.md` with notable user-facing, architecture, repository, or release-process changes.
- Follow `docs/architecture/repository-architecture.md` and `docs/engineering/coding-standards.md`.
- Aim for source files under 250 lines. Review files over 350 lines and split files over 500 lines unless generated, schema/spec content, or explicitly documented as an exception.
- Prefer KISS and DRY with judgment: remove meaningful duplication, but do not introduce abstractions for a single caller.
