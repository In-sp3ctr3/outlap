# RaceWeek Strategist v1 Gate Matrix

| Harness | Phase | Required Artifact | Acceptance Criteria | Evidence | Status |
|---|---|---|---|---|---|
| Spec/Product | Scope classification | Supplied docs plus this matrix | v1 scope and accepted slice are explicit | `docs/*`, `MASTER_SPEC.md` | complete |
| System Design | Architecture baseline | ADRs and implementation notes | Next.js + FastAPI + deterministic core preserved | `docs/adrs/*`, `docs/04_ARCHITECTURE.md` | complete |
| Repository Architecture | Monorepo scaffold | pnpm workspace + apps/packages tree | Web/API/fixtures/docs separated | `package.json`, `pnpm-workspace.yaml`, `apps/*`, `packages/*` | complete |
| Engineering | Testable vertical slice | Unit/API/web/e2e tests | Rules, projections, optimizer, provider/data failure flows covered | `apps/api/tests`, `apps/web/tests` | in progress |
| Security | Local-first guardrails | Redaction, fake provider, no official assets | Secrets stay server-side; no auto-transfer path | API provider tests and UI disclaimer | in progress |
| Frontend | Product cockpit UI | Responsive pages and shared components | Primary routes and required states exist | Playwright demo/manual/failure flows | in progress |
| SEO | Public app basics | Metadata and disclaimer | App has descriptive metadata and legal text | `apps/web/app/layout.tsx` | in progress |
| Repo Hygiene | Public-ready baseline | README, license/security/contributing, CI, templates, changelog, standards | Existing docs preserved; CI skeleton added; commit cadence defined | `.github/workflows/check.yml`, `CHANGELOG.md`, `docs/engineering/coding-standards.md` | complete |

## Accepted Slice

The first implementation slice is a complete local demo product: deterministic rules, projections, optimizer, manual imports, data health degradation, fake provider fallback, league analysis, and a polished multi-page UI. Live upstream connectors and full provider SDK calls are represented by typed adapters/fallbacks and documented as follow-up hardening because they require real upstream credentials and longer maintenance validation.
