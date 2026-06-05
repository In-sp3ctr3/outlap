from __future__ import annotations

from raceweek.core.models import StrategyMode

STRATEGY_WEIGHTS: dict[str, dict[str, float]] = {
    "safe": {
        "expected": 0.60,
        "floor": 0.30,
        "ceiling": 0.05,
        "riskPenalty": 0.25,
        "budgetGrowth": 0.05,
        "differential": 0.00,
    },
    "balanced": {
        "expected": 0.75,
        "floor": 0.10,
        "ceiling": 0.10,
        "riskPenalty": 0.12,
        "budgetGrowth": 0.08,
        "differential": 0.05,
    },
    "aggressive": {
        "expected": 0.55,
        "floor": 0.00,
        "ceiling": 0.30,
        "riskPenalty": 0.03,
        "budgetGrowth": 0.05,
        "differential": 0.20,
    },
    "budget_builder": {
        "expected": 0.50,
        "floor": 0.05,
        "ceiling": 0.05,
        "riskPenalty": 0.10,
        "budgetGrowth": 0.40,
        "differential": 0.00,
    },
    "differential": {
        "expected": 0.55,
        "floor": 0.05,
        "ceiling": 0.20,
        "riskPenalty": 0.08,
        "budgetGrowth": 0.05,
        "differential": 0.30,
    },
    "chip_optimized": {
        "expected": 0.72,
        "floor": 0.08,
        "ceiling": 0.14,
        "riskPenalty": 0.10,
        "budgetGrowth": 0.05,
        "differential": 0.08,
    },
}


def weights_for(strategy_mode: StrategyMode) -> dict[str, float]:
    return STRATEGY_WEIGHTS.get(strategy_mode, STRATEGY_WEIGHTS["balanced"])
