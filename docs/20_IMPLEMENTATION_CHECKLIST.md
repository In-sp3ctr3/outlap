# 20 — v1 Acceptance Checklist

Use this as the release gate for v1.0.0.

## Product

- [ ] Setup wizard works in demo mode.
- [ ] Setup wizard works with manual team import.
- [ ] Dashboard shows next event, team state, recommendation, and data health.
- [ ] Market table supports sorting/filtering/comparison.
- [ ] Optimizer returns safe/balanced/aggressive/budget/differential/chip modes.
- [ ] Race Week page shows sessions, weather, race-control, news, and stale-data states.
- [ ] AI Strategist works with fake provider and at least one real configured provider.
- [ ] League analysis works with imported demo league data.
- [ ] Settings page manages providers, data sources, rules, privacy, import/export.

## Data

- [x] Manual import validates JSON and CSV.
- [ ] Fantasy connector is optional and read-only.
- [x] OpenF1 connector works with fixture/mocked tests.
- [ ] Jolpica connector works with fixture/mocked tests.
- [ ] FastF1 adapter works with cache path.
- [ ] News connector stores metadata/summary only.
- [x] Source snapshots are recorded.
- [x] Data health is visible in UI.

## Rules/optimizer

- [ ] 5-driver/2-constructor constraints tested.
- [ ] Budget cap tested.
- [ ] Transfer penalties tested.
- [ ] Net-transfer counting tested.
- [ ] All chips tested.
- [ ] Optimizer deterministic ordering tested.
- [ ] Recommendations include provenance.

## AI

- [ ] Provider registry supports required providers.
- [ ] No provider key is exposed to browser.
- [ ] Fake provider test suite passes.
- [ ] AI refuses auto-transfer requests.
- [ ] AI references recommendation IDs for transfer advice.
- [ ] Fallback template works without AI.

## UI/UX

- [ ] Responsive desktop/tablet/mobile.
- [ ] Dark mode.
- [ ] Empty/loading/error states.
- [ ] Accessibility basics.
- [ ] No official logos/assets.
- [ ] Unofficial disclaimer in footer/about.

## Engineering

- [ ] `make setup` works from fresh clone.
- [ ] `make dev` starts app.
- [ ] `make check` passes.
- [ ] CI runs lint/typecheck/tests/e2e.
- [ ] Lockfiles committed.
- [ ] Dependency audit reviewed.
- [ ] Docs updated.
- [ ] Security policy present.
- [ ] License selected.

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
- [ ] Full v1 connector, provider, optimizer, projection, UI-state, and release gates remain open.
