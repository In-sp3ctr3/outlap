# 20 — v1 Acceptance Checklist

Use this as the release gate for v1.0.0.

## Product

- [x] Real-data onboarding starts empty without demo fallback.
- [x] Onboarding selects Team 1, Team 2, and Team 3 from loaded market/catalog assets.
- [x] Dashboard shows next event, team state, recommendation, and data health.
- [x] Market table supports sorting/filtering/comparison.
- [x] Optimizer returns safe/balanced/aggressive/budget/differential/chip modes.
- [x] Race Week page shows sessions, weather, race-control, news, and stale-data states.
- [x] AI Strategist works with fake provider and at least one real configured provider.
- [x] League view degrades to empty state until real/imported league data is available.
- [x] Settings page manages providers, data sources, rules, privacy, import/export.

## Data

- [x] Manual import validates JSON and CSV.
- [x] Fantasy connector is optional and read-only.
- [x] OpenF1 connector works with fixture/mocked tests.
- [x] Jolpica connector works with fixture/mocked tests.
- [x] FastF1 adapter works with cache path.
- [x] News connector stores metadata/summary only.
- [x] Source snapshots are recorded.
- [x] Data health is visible in UI.

## Rules/optimizer

- [x] 5-driver/2-constructor constraints tested.
- [x] Budget cap tested.
- [x] Transfer penalties tested.
- [x] Net-transfer counting tested.
- [x] All chips tested.
- [x] Optimizer deterministic ordering tested.
- [x] Recommendations include provenance.
- [x] Custom optimizer weights affect deterministic ranking.
- [x] Recommendation run IDs are request-specific and reproducible.

## AI

- [x] Provider registry supports required providers.
- [x] No provider key is exposed to browser.
- [x] Fake provider test suite passes.
- [x] AI refuses auto-transfer requests.
- [x] AI references recommendation IDs for transfer advice.
- [x] Fallback template works without AI.

## UI/UX

- [x] Responsive desktop/tablet/mobile.
- [x] Dark mode.
- [x] Empty/loading/error states.
- [x] Accessibility basics.
- [x] No official logos/assets.
- [x] Unofficial disclaimer in footer/about.

## Engineering

- [x] `make setup` works from fresh clone.
- [x] `make dev` starts app.
- [x] `make check` passes.
- [x] CI runs lint/typecheck/tests/e2e.
- [x] CodeQL workflow is configured.
- [x] Lockfiles committed.
- [x] Dependency audit reviewed.
- [x] Docs updated.
- [x] Security policy present.
- [x] License selected.

## Milestone Evidence

- [x] Milestone 1 DuckDB migrations apply cleanly in API tests.
- [x] Milestone 1 demo fixtures seed into DuckDB via `raceweek seed-demo`.
- [x] Milestone 1 demo source snapshots are recorded with content hashes and raw JSON payloads.
- [x] Milestone 1 projection and recommendation runs persist and reload with provenance.
- [x] Manual team, market, and league imports validate JSON/CSV inputs before storage.
- [x] Manual import warnings report unknown JSON fields and CSV columns without failing the import.
- [x] Manual import rejects duplicate lineup assets and non-numeric market prices.
- [x] Fantasy score CSV import validates numeric fields and persists score snapshots.
- [x] OpenF1 mocked session-context connector degrades gracefully and persists sanitized source snapshots.
- [x] Jolpica mocked season-context connector normalizes schedule/results/standings and persists sanitized source snapshots.
- [x] RSS/news connector stores metadata and feed summaries without full article bodies.
- [x] FastF1 adapter enables the configured cache path and stores aggregate session summaries only.
- [x] Optional fantasy connector uses documented GET endpoints and redacts session tokens from persisted metadata.
- [x] Projection contribution breakdowns and CLI backtests use deterministic fixture error metrics.
- [x] Optimizer uses the pinned OR-Tools CP-SAT path when available and falls back to brute force deterministically.
- [x] Custom optimizer weights and request fingerprints persist with recommendation runs.
- [x] Chip scoring simulation covers regular boost, 3x Boost, Autopilot, No Negative, Wildcard, Limitless, and Final Fix.
- [x] Provider registry, OpenAI-compatible adapter path, fake provider tests, agent refusal, recommendation ID citation, and fallback template are covered.
- [x] UI-state pass covers responsive navigation, skip link, announced loading/empty/error states, working market/optimizer controls, dynamic provider selection, and disclaimer/no-official-asset checks.
- [x] Release gate pass covers `make setup`, `make dev`, `make check`, CI workflow health, lockfiles, dependency audits, security policy, and MIT license.
- [x] Official SDK adapter pass covers OpenAI, Anthropic, Gemini, Mistral, and Ollama with mocked SDK-client tests.
- [x] Product acceptance pass covers real-data empty state, market load, Team 1/2/3 selection, dashboard, market sort/filter/lock/compare, race-week session/weather/race-control/stale data, league empty/imported states, settings provider/import controls, and fake/failing AI provider browser flows.
- [x] Live configured-provider smoke completed against local Ollama with `smollm2:135m`.
- [x] OSS presentation pass covers README badges, generated header asset, and CodeQL static analysis workflow.
