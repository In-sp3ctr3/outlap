# Security Test Plan

## Automated Checks

- `git grep` secret-pattern scan over committed source/docs excluding large imported specs.
- API test: provider failure returns fallback and `canMutateFantasyAccount=false`.
- API test: data-source failure returns degraded state and optimizer still returns deterministic recommendations.
- Playwright: provider failure path remains visible and manual-only.
- Playwright: degraded data health remains visible and optimizer works from local snapshot.
- `make check`: lint, typecheck, unit/API tests, frontend unit test, and E2E.

## Future Live-Connector Checks

- Redact auth headers and session tokens from logs/snapshots.
- Mock non-200, invalid JSON, and schema drift for each connector.
- Verify provenance records exclude secrets.
- Verify provider prompt payloads contain only minimum recommendation context.
