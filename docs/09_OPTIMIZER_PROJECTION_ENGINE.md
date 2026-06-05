# 09 — Optimizer and Projection Engine

## Source-of-truth hierarchy

1. Rules engine determines legality.
2. Projection engine estimates points and uncertainty.
3. Optimizer ranks legal options.
4. AI explains optimizer output.

The AI must never bypass steps 1–3.

## Rules engine

Rules must be stored as versioned JSON and loaded into typed models.

Example ruleset:

```json
{
  "rulesetId": "fantasy_2026_v1",
  "season": 2026,
  "lineup": {
    "drivers": 5,
    "constructors": 2
  },
  "budget": {
    "costCapMillions": 100.0
  },
  "transfers": {
    "freeTransfersPerRound": 2,
    "maxCarriedTransfers": 1,
    "penaltyPointsPerExtraTransfer": 10,
    "countingMode": "net_asset_changes"
  },
  "chips": [
    "2x_boost",
    "3x_boost",
    "autopilot",
    "no_negative",
    "wildcard",
    "limitless",
    "final_fix"
  ]
}
```

## Transfer counting

Implement as pure function:

```python
def calculate_net_transfers(previous_asset_ids: set[str], proposed_asset_ids: set[str]) -> int:
    removed = previous_asset_ids - proposed_asset_ids
    added = proposed_asset_ids - previous_asset_ids
    if len(removed) != len(added):
        raise InvalidLineupTransition("lineup size changed unexpectedly")
    return len(added)
```

For standard transfers:

```python
penalty = max(0, net_transfers - free_transfers) * penalty_points_per_extra_transfer
```

Chip overrides:

- Wildcard: transfer penalty becomes 0 for the event, but budget cap remains.
- Limitless: transfer penalty becomes 0 and budget cap constraint is disabled for that event; future team reversion must be represented in assumptions.
- Final Fix: one late driver change scenario; it does not change regular boost alone.
- No Negative: lower-bound score for selected assets/team is floored according to configured rules.
- Autopilot: 2x boost assigned to highest-scoring eligible driver after scoring simulation.
- 3x Boost: selected eligible driver receives 3x instead of normal boost according to ruleset.

## Projection engine

### v1 default model: transparent weighted projection

For each asset/event:

```text
expected_points =
  w_recent3 * rolling_fantasy_points_3
+ w_recent5 * rolling_fantasy_points_5
+ w_quali * qualifying_form
+ w_race_pace * race_pace_form
+ w_constructor * constructor_form
+ w_circuit * circuit_fit_score
+ w_weather * weather_adjustment
+ w_news * news_adjustment
+ w_penalty * penalty_adjustment
+ base_asset_prior
```

Default weights should be configuration, not constants scattered through code.

Example default weights:

```json
{
  "rolling_fantasy_points_3": 0.30,
  "rolling_fantasy_points_5": 0.20,
  "qualifying_form": 0.15,
  "race_pace_form": 0.15,
  "constructor_form": 0.08,
  "circuit_fit_score": 0.04,
  "weather_adjustment": 0.03,
  "news_adjustment": 0.03,
  "penalty_adjustment": 0.02
}
```

These are initial defaults. The implementation must support backtesting and user tuning.

### Projection outputs

For each asset:

- expected points;
- floor/P10;
- ceiling/P90;
- confidence;
- risk score;
- projected price delta;
- contribution breakdown;
- assumptions.

### Confidence calculation

Confidence should decrease when:

- data is stale;
- session data is missing;
- news risk is high;
- weather risk is high;
- asset has high DNF/penalty variance;
- projection model has low historical accuracy for similar events.

## Feature engineering

Required v1 features:

| Feature | Description |
|---|---|
| `rolling_points_3` | Rolling average over last 3 fantasy events |
| `rolling_points_5` | Rolling average over last 5 fantasy events |
| `points_per_million` | Expected points divided by price |
| `price_delta_3` | Recent price change trend |
| `quali_form` | Recent qualifying/session rank feature |
| `race_pace_form` | Recent race/lap/session pace feature |
| `constructor_form` | Constructor-level recent performance |
| `teammate_delta` | Driver vs teammate relative feature |
| `reliability_score` | DNF/mechanical/constructor risk proxy |
| `penalty_risk` | Grid/race-control/news penalty flag |
| `weather_risk` | Rain/temperature/wind uncertainty proxy |
| `news_risk` | News-derived risk flag score |
| `ownership_pct` | Selection/ownership if available |
| `differential_score` | Inverse ownership adjusted for projection |

## Optimizer formulation

Decision variable:

```text
x_a = 1 if asset a is selected, otherwise 0
```

Constraints:

```text
sum(x_driver) = 5
sum(x_constructor) = 2
sum(price_a * x_a) <= cost_cap, except Limitless
locked assets: x_a = 1
banned assets: x_a = 0
chip constraints apply
```

Transfer variables can be derived from selected assets compared to current team.

Base objective:

```text
maximize expected_net_score =
  lineup_expected_points
- transfer_penalty_points
+ budget_growth_weight * expected_budget_delta
+ upside_weight * ceiling_points
- risk_weight * risk_score
+ differential_weight * differential_score
```

## Strategy modes

| Mode | Objective behavior |
|---|---|
| safe | Higher weight on floor/confidence, lower risk |
| balanced | Max expected net points with moderate risk penalty |
| aggressive | Higher ceiling/upside and differential weight |
| budget_builder | Weight expected price growth and future flexibility |
| differential | Weight low ownership and league gaps |
| chip_optimized | Compare all available chip scenarios |
| custom | User-defined weights |

Default weights:

```json
{
  "safe": {
    "expected": 0.60,
    "floor": 0.30,
    "ceiling": 0.05,
    "riskPenalty": 0.25,
    "budgetGrowth": 0.05,
    "differential": 0.00
  },
  "balanced": {
    "expected": 0.75,
    "floor": 0.10,
    "ceiling": 0.10,
    "riskPenalty": 0.12,
    "budgetGrowth": 0.08,
    "differential": 0.05
  },
  "aggressive": {
    "expected": 0.55,
    "floor": 0.00,
    "ceiling": 0.30,
    "riskPenalty": 0.03,
    "budgetGrowth": 0.05,
    "differential": 0.20
  },
  "budget_builder": {
    "expected": 0.50,
    "floor": 0.05,
    "ceiling": 0.05,
    "riskPenalty": 0.10,
    "budgetGrowth": 0.40,
    "differential": 0.00
  },
  "differential": {
    "expected": 0.55,
    "floor": 0.05,
    "ceiling": 0.20,
    "riskPenalty": 0.08,
    "budgetGrowth": 0.05,
    "differential": 0.30
  }
}
```

## Recommendation option output

Each option must include:

```json
{
  "optionId": "recopt_...",
  "rank": 1,
  "strategyMode": "balanced",
  "chipAction": "none",
  "transfers": [
    {"assetOutId": "asset_a", "assetInId": "asset_b", "reason": "Higher projected net points"}
  ],
  "expectedGrossPoints": 184.2,
  "transferPenaltyPoints": 0,
  "expectedNetPoints": 184.2,
  "budgetUsedMillions": 99.4,
  "budgetRemainingMillions": 0.6,
  "expectedBudgetDeltaMillions": 0.2,
  "riskScore": 0.34,
  "confidence": 0.72,
  "summary": "Use one free transfer and save chips.",
  "rationale": ["..."],
  "assumptions": ["..."],
  "warnings": ["..."]
}
```

## Brute-force fallback

Because the asset universe is small, brute-force is acceptable for many runs:

```python
for driver_combo in combinations(drivers, 5):
    for constructor_combo in combinations(constructors, 2):
        lineup = driver_combo + constructor_combo
        if not is_legal(lineup):
            continue
        score = score_lineup(lineup)
        collect(score)
```

Use pruning:

- filter inactive assets;
- apply locked/banned assets first;
- skip over-budget early;
- cap returned options to top N after stable sorting.

## Determinism

For the same input, the optimizer must produce the same ranked output.

Tie-breakers:

1. higher expected net points;
2. lower risk;
3. higher confidence;
4. more budget remaining;
5. fewer transfers;
6. lexicographic asset IDs.

## Backtesting

v1 must include a backtesting page or CLI command:

```bash
uv run raceweek backtest --season 2025 --strategy balanced
```

Backtest output:

- projected vs actual points;
- mean absolute error;
- strategy rank vs baseline;
- chip timing simulation;
- model calibration chart data.

## Test cases

Required unit tests:

- legal lineup with 5 drivers/2 constructors passes;
- duplicate asset fails;
- over-budget lineup fails;
- Limitless ignores budget for one event;
- Wildcard removes transfer penalty;
- standard extra transfers cost penalty;
- net-transfer counting ignores reorder;
- No Negative floors negative scores;
- Autopilot assigns boost to top actual/projection depending simulation mode;
- optimizer returns deterministic ordering;
- locked assets remain selected;
- banned assets are excluded;
- recommendation includes provenance IDs.
