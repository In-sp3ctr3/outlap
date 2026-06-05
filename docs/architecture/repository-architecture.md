# Repository Architecture

## Forces

- Public open-source project with outside contributors expected later.
- Two deployment units: a Next.js web app and a FastAPI API.
- Deterministic fantasy strategy domain where rules, projections, and optimizer behavior must be testable outside framework code.
- Local-first default with demo fixtures and DuckDB-ready storage.
- Provider connectors and live data sources must sit behind explicit adapter boundaries.
- The repository should read like a human-maintained project: small files, clear modules, normal commits, and no generated-code branding.

## Selected Pattern

Use a pnpm workspace monorepo with a thin-app, deterministic-core structure:

```text
apps/api/src/raceweek/
  api/          FastAPI routes and request/response wiring
  core/         Pure rules, projection, optimizer, and domain models
  storage/      Demo and DuckDB persistence adapters
  connectors/   External data adapters, added behind ports
  jobs/         Sync and scheduled work
  agents/       AI provider adapters and read-only tool orchestration
apps/web/
  app/          Next.js routes
  components/   UI components split by page/domain
  lib/          API client, formatting, and browser-safe helpers
packages/
  fixtures/     Synthetic demo data
```

This keeps framework code thin and lets the most important behavior run in direct unit tests.

## Rejected Patterns

- Single full-stack app: weaker fit for Python optimization, connectors, and data tooling.
- Flat repository: too ambiguous once API, web, contracts, fixtures, CI, and docs coexist.
- Heavy Clean Architecture ceremony in every module: unnecessary for v1 and likely to create one-caller abstractions.

## Boundary Rules

- `apps/api/src/raceweek/core` must not import FastAPI, DuckDB, HTTP clients, provider SDKs, or environment settings.
- API route handlers should validate input, call use cases/core helpers, and return typed responses.
- AI/provider code may explain recommendations but must not calculate final lineups, transfer penalties, or budgets.
- Web components may call `apps/web/lib/api.ts`; page components should not duplicate fetch logic.
- Fixtures must be synthetic or explicitly license-safe.
- Generated or imported specs stay in `api/`, `schemas/`, `docs/`, and `MASTER_SPEC.md`.

## File Standards

- Aim for source files under 250 lines.
- A file over 350 lines needs a clear reason to stay together.
- A file over 500 lines should be split before commit unless it is generated, a schema, a spec, or an accepted exception documented in the PR.
- Split by reason to change, not by aesthetic category.
- Prefer concrete names over broad `utils` modules.
- Add comments only where they clarify non-obvious domain rules or safety constraints.

## Test Placement

- Backend domain tests live in `apps/api/tests`.
- Frontend unit tests live beside the browser-safe helper or component area they exercise.
- Playwright tests live in `apps/web/tests/e2e`.
- Fixtures used by both apps live in `packages/fixtures`.

## Commit And Review Standards

- Keep docs/spec import, repo hygiene, backend domain, API, frontend UI, tests, and CI in separate commits.
- Use concise Conventional Commit messages.
- Do not add tool branding, prompt transcripts, generated-code disclaimers, or AI co-author trailers.
- Before a commit, run the smallest relevant check for the files changed; before pushing, run the full agreed check suite or document any local blocker.
