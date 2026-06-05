# Security Audit

## Completed

- No auto-transfer route or mutating AI tool exists.
- Provider list exposes configuration status only, not secret values.
- Chat fallback path is explicit and read-only.
- Data-source degradation path is covered by API and Playwright tests.
- Fixtures use fictional teams, drivers, constructors, news, and league data.
- `.env`, local DuckDB files, caches, build output, and Playwright artifacts are ignored.
- GitHub workflows include main checks and a Gitleaks secret-scan workflow.
- Local `git grep` secret-pattern scan returned no matches.
- GitHub repository metadata was set, unused Wiki/Projects were disabled, topics were added, and automatic branch deletion after merge was enabled.
- `main` branch protection requires API, Web, E2E, and gitleaks checks; force pushes/deletion are blocked; linear history and conversation resolution are required; admin bypass remains available for solo-maintainer safety.

## Accepted Risks

- Real provider adapters and live connectors are not fully implemented in this demo slice; they must pass provider/connector-specific negative tests before public release.
- The current API stores demo state in memory for E2E speed. Persistent DuckDB repositories are scaffolded but not yet the default runtime store.
