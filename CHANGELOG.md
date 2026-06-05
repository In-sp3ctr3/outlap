# Changelog

All notable changes to RaceWeek Strategist will be documented here.

This project follows Semantic Versioning once the first public release is tagged.

## [Unreleased]

### Added

- Imported the v1 product, architecture, security, testing, API, schema, and ADR documentation package.
- Added the initial monorepo scaffold for the FastAPI API, Next.js web app, synthetic fixtures, and implementation verification records.
- Added public repository hygiene files, coding standards, and CI/dependency-update configuration.
- Added DuckDB-backed demo persistence, source snapshot storage, projection/recommendation run storage, and the `raceweek seed-demo` command.
- Added manual import validation for JSON and CSV team, market, and league snapshots.
- Added manual fantasy score CSV import, score persistence, and score listing endpoints.
- Added a mocked OpenF1 session-context connector with provenance-safe snapshot persistence.
- Aligned data-source health statuses with the public `ok`/`degraded` API contract.
- Added a mocked Jolpica season-context connector for schedule, results, qualifying, sprint, and standings data.
- Added a metadata-only RSS/news connector that drops full article bodies from persisted snapshots.
- Added a FastF1 cache adapter that returns aggregate session summaries without raw telemetry.
- Added an optional read-only fantasy connector using documented GET endpoints with token redaction.
- Added deterministic projection backtesting with real fixture error metrics in the CLI.
- Added a pinned OR-Tools optimizer path with brute-force fallback and optimizer provenance in contracts.
- Added custom optimizer weights with request-specific recommendation fingerprints and persisted request context.
- Added deterministic chip scoring for regular boost, 3x Boost, Autopilot, No Negative, and Final Fix constraints.
- Added a typed AI provider registry, OpenAI-compatible adapter path, fake provider tests, browser-safe provider config responses, and read-only agent guardrails.
