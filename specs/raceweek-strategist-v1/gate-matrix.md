# RaceWeek Strategist v1 Gate Matrix

| Harness | Phase | Required Artifact | Acceptance Criteria | Evidence | Status |
|---|---|---|---|---|---|
| Spec/Product | Scope classification | Supplied docs plus this matrix | v1 scope and accepted slice are explicit | `docs/*`, `MASTER_SPEC.md` | complete |
| System Design | Architecture baseline | ADRs and implementation notes | Next.js + FastAPI + deterministic core preserved | `docs/adrs/*`, `docs/04_ARCHITECTURE.md` | complete |
| Repository Architecture | Monorepo scaffold | pnpm workspace + apps/packages tree | Web/API/fixtures/docs separated | `package.json`, `pnpm-workspace.yaml`, `apps/*`, `packages/*` | complete |
| Engineering | Contracts/database slice | DuckDB migrations, repository, seed command, storage/API tests | Migrations apply, fixtures load, projection/recommendation runs persist with provenance | `apps/api/src/raceweek/storage/*`, `apps/api/tests/test_storage.py`, `apps/api/tests/test_api.py`, `uv run raceweek seed-demo` | complete for Milestone 1 |
| Engineering | Manual import connector slice | Manual parser, API routes, OpenAPI request schemas, synthetic CSV fixtures | Team/market/league JSON or CSV imports validate before storage and report warnings | `apps/api/src/raceweek/connectors/manual*.py`, `apps/api/tests/test_manual_import.py`, `api/openapi.yaml` | complete for team/market/league |
| Engineering | Remaining v1 slices | Unit/API/web/e2e tests per milestone | Fantasy score CSV storage, live/mocked data connectors, full projection engine, OR-Tools path, real provider adapters, complete UI states, release gates | `docs/14_IMPLEMENTATION_PLAN.md`, `docs/20_IMPLEMENTATION_CHECKLIST.md` | in progress |
| Security | Local-first guardrails | Threat model, requirements, test plan, audit | Secrets stay server-side; no auto-transfer path | `specs/raceweek-strategist-v1/security/*`, API/provider tests, UI disclaimer | complete |
| Frontend | Product cockpit UI | Responsive pages and shared components | Primary routes and required states exist | Playwright demo/manual/failure flows | complete |
| SEO | Public app basics | Metadata and disclaimer | App has descriptive metadata and legal text | `apps/web/app/layout.tsx` | complete |
| Repo Hygiene | Public-ready baseline | README, license/security/contributing, CI, templates, changelog, standards | Existing docs preserved; CI skeleton added; commit cadence defined | `.github/workflows/check.yml`, `CHANGELOG.md`, `docs/engineering/coding-standards.md` | complete |

## Current Implemented Scope

The current implementation includes repository hygiene, a local demo product, and the Milestone 1 DuckDB contracts/database slice. Deterministic rules, projections, optimizer, manual imports, data health degradation, fake provider fallback, league analysis, and the multi-page UI are present for demo workflows.

The full v1 spec is not yet complete. Live upstream connectors, full provider SDK calls, full projection feature/backtest engine, OR-Tools optimizer path, and release-grade QA/docs remain open work.
