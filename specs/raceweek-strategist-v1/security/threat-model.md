# Security Threat Model

## Risk Classification

RaceWeek Strategist v1 is local-first and demo-safe by default. The sensitive surfaces are provider API keys, optional future read-only fantasy connector tokens, imported fantasy team data, league data, external connector payloads, and AI prompts that include strategy context.

Verification target: Level 1 for the current local demo slice, with Level 2 requirements documented for future account/hosted/live-connector work.

## Assets

- Provider API keys and base URLs.
- User team snapshots, league snapshots, and recommendation history.
- Source snapshots and provenance metadata.
- Local DuckDB file under `data/`.
- Prompt context passed to AI providers.

## Actors

- Local user running the app.
- Contributor opening pull requests.
- External data provider or unstable upstream endpoint.
- AI provider endpoint.
- Malicious webpage or process attempting to reach local services.

## Trust Boundaries

- Browser to FastAPI over localhost.
- FastAPI to local storage.
- FastAPI to future external connectors.
- FastAPI to future AI provider SDKs.
- Repository fixtures and tests to public Git history.

## Abuse Cases And Mitigations

- Secret leakage to browser: provider configs only expose `keyConfigured`, not secret values.
- Secret leakage to logs/fixtures: `.env*` ignored except `.env.example`; tests use synthetic fixtures.
- AI submits transfers: no API route exists for auto-transfer execution; chat response declares `canMutateFantasyAccount=false`.
- Broken connector crashes dashboard: sync failure creates degraded data-source status and optimizer still uses local snapshots.
- Official/protected asset misuse: fixtures are fictional and docs/UI include unofficial disclaimer.
- Cross-test state bleed: Playwright resets demo API state before each test and runs one worker because the demo API is in-memory.

## Residual Risks

- Live provider adapters are represented by fake/fallback paths in this slice; each real adapter needs provider-specific tests before release.
- Localhost CORS is permissive for the web dev origin only; hosted deployment needs a separate CORS/header review.
- DuckDB persistence is scaffolded but not fully exercised by the demo state service yet.
