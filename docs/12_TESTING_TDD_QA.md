# 12 — Testing, TDD, and QA Strategy

## Testing philosophy

The project is a strategy engine with a polished UI. Bugs can create bad decisions, so domain correctness matters more than superficial coverage.

Use test-driven development for:

- rules engine;
- transfer counting;
- chip simulation;
- optimizer constraints;
- projection feature calculations;
- provider/tool guardrails;
- connector normalization.

## Test pyramid

```text
                 E2E tests
              Playwright UI flows
          ─────────────────────────
          API integration tests
       FastAPI + temporary DuckDB
   ───────────────────────────────────
   Domain and connector unit tests
 Rules • optimizer • projections • schemas
```

## Coverage targets

| Area | Minimum |
|---|---:|
| Rules engine | 95% |
| Optimizer | 95% |
| Projection feature engine | 90% |
| Connectors normalization | 85% |
| API routes | 80% |
| Web business logic | 75% |
| UI snapshots/visual checks | Best effort |

Coverage alone is not enough. Edge-case tests are required.

## Required backend test suites

### Rules engine tests

- legal lineup passes;
- too few drivers fails;
- too many constructors fails;
- duplicate assets fail;
- over-budget lineup fails;
- missing price fails with clear error;
- transfer count ignores order;
- transfer count equals net asset changes;
- extra transfers apply penalty;
- Wildcard zeroes transfer penalty;
- Limitless ignores budget cap for event;
- No Negative floors negative scores;
- 3x boost applies configured multiplier;
- Autopilot assigns boost according to configured simulation;
- Final Fix allows only one late driver change.

### Optimizer tests

- returns only legal lineups;
- honors locked assets;
- honors banned assets;
- does not exceed budget except Limitless;
- ranks by deterministic tie-breakers;
- includes transfer penalty in net score;
- returns no options with useful error when constraints impossible;
- strategy modes change ranking as expected;
- option output includes rationale, assumptions, and warnings.

### Projection tests

- rolling averages calculate correctly;
- missing data lowers confidence;
- stale source lowers confidence;
- risk flags increase risk score;
- contribution breakdown sums to expected score within tolerance;
- price delta model handles missing history;
- model version is stored.

### Connector tests

Use `respx` for HTTP mocking.

- happy path normalizes expected fixture;
- non-200 response creates degraded/error status;
- invalid JSON handled;
- rate-limit headers handled;
- secrets redacted;
- raw snapshot created;
- schema change produces warning instead of silent corruption.

### API tests

- OpenAPI schema validates;
- endpoints return expected status codes;
- invalid request bodies return typed error envelope;
- recommendations create run records;
- data-source statuses are returned;
- chat endpoint works with fake provider.

### AI/provider tests

Do not call live providers in CI.

Use fake provider fixtures to test:

- provider registry;
- provider config validation;
- tool-call orchestration;
- no secret leakage;
- no auto-transfer behavior;
- stale data warning;
- deterministic fallback template when provider fails.

## Required frontend test suites

### Unit/component tests

- `RecommendationCard` renders all metrics;
- `RiskMeter` handles low/medium/high;
- `DataFreshnessBadge` handles stale/degraded/error;
- setup wizard validates provider fields;
- market filters and sort state;
- locked/banned asset controls.

### Playwright E2E flows

1. Demo first run.
   - launch app;
   - complete setup in demo mode;
   - see dashboard;
   - open optimizer;
   - generate recommendation;
   - open AI Strategist with fake provider.

2. Manual import.
   - import fixture team;
   - import market;
   - run projections;
   - run optimizer;
   - compare two recommendation cards.

3. Data-source failure.
   - simulate failed connector;
   - show data health degraded;
   - optimizer still works with last snapshot or manual data.

4. Provider failure.
   - configure fake provider failure;
   - chat shows fallback/error state;
   - deterministic recommendation remains visible.

## Fixtures

Fixtures must be synthetic or license-safe. Do not commit real official data unless clearly permitted.

Required fixture files:

```text
packages/fixtures/
  fantasy_market_demo.json
  fantasy_team_demo.json
  fantasy_scores_demo.csv
  race_calendar_demo.json
  openf1_session_demo.json
  news_demo.json
  league_demo.json
```

Use fictional names in fixtures by default:

- Driver Alpha;
- Driver Bravo;
- Constructor One;
- Constructor Two.

This avoids redistribution of proprietary current data.

## Golden tests

Recommendation output should have golden tests:

```text
tests/golden/balanced_recommendation.json
tests/golden/chip_limitless_recommendation.json
tests/golden/differential_recommendation.json
```

Golden tests must ignore volatile fields:

- generated timestamp;
- run ID;
- snapshot ID if generated.

## Property-style tests

Even without adding a property-testing dependency, create randomized tests for:

- lineup legality;
- transfer counting symmetry;
- optimizer never returns banned assets;
- net score never ignores transfer penalty;
- budget cap always enforced in non-Limitless modes.

## QA checklist before release

- Fresh clone setup passes.
- Demo mode works offline except package install.
- Manual import works.
- Fantasy connector disabled state works.
- OpenF1/Jolpica connector tests pass with fixtures.
- AI provider fake tests pass.
- Ollama local config path documented.
- No official assets/logos in repo.
- No secrets in repo or logs.
- `make check` passes.
- Playwright E2E passes.
- README and disclaimer present.
- License and security policy present.

## CI pipeline

Required jobs:

```text
lint-python
lint-web
typecheck-python
typecheck-web
test-python
test-web
e2e-demo
openapi-validate
schema-validate
secret-scan
dependency-audit
```

CI must run with fixture/demo data only. Live connector tests may run in a separate scheduled workflow with maintainer-provided secrets, but they must not block normal contributor PRs.

## Definition of done

A pull request is not done until:

- tests are included;
- docs are updated;
- fixtures are safe;
- no secrets/log leaks;
- UI has error/loading/empty state;
- source provenance is recorded when data is involved;
- accessibility basics are considered;
- `make check` passes locally and in CI.
