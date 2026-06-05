from __future__ import annotations

from importlib import import_module
from typing import Any, cast

from raceweek.core.models import FantasyAsset, Projection, StrategyMode
from raceweek.core.strategy import weights_for

ORTOOLS_OPTIMIZER_VERSION = "ortools_cp_sat_v1"


def solve_lineups_with_ortools(
    *,
    assets: list[FantasyAsset],
    projections: dict[str, Projection],
    current_asset_ids: set[str],
    locked_asset_ids: set[str],
    strategy_mode: StrategyMode,
    custom_weights: dict[str, float],
    cost_cap_millions: float,
    free_transfers: int,
    penalty_points: float,
    chip_action: str | None,
    max_options: int,
) -> list[tuple[str, ...]]:
    cp_model = _load_cp_model()
    if cp_model is None:
        return []

    candidates = sorted(
        [asset for asset in assets if asset.asset_id in projections],
        key=lambda asset: asset.asset_id,
    )
    driver_ids = [asset.asset_id for asset in candidates if asset.asset_type == "driver"]
    constructor_ids = [
        asset.asset_id for asset in candidates if asset.asset_type == "constructor"
    ]
    if len(driver_ids) < 5 or len(constructor_ids) < 2:
        return []

    model = cp_model.CpModel()
    decision_vars = {
        asset.asset_id: model.NewBoolVar(_var_name(asset.asset_id))
        for asset in candidates
    }
    model.Add(sum(decision_vars[asset_id] for asset_id in driver_ids) == 5)
    model.Add(sum(decision_vars[asset_id] for asset_id in constructor_ids) == 2)

    for asset_id in locked_asset_ids:
        if asset_id not in decision_vars:
            return []
        model.Add(decision_vars[asset_id] == 1)

    if chip_action != "limitless":
        model.Add(
            sum(
                _money_units(asset.price_millions) * decision_vars[asset.asset_id]
                for asset in candidates
            )
            <= _money_units(cost_cap_millions)
        )

    transfer_count = model.NewIntVar(0, 7, "transfer_count")
    model.Add(
        transfer_count
        == sum(
            decision_vars[asset.asset_id]
            for asset in candidates
            if asset.asset_id not in current_asset_ids
        )
    )
    excess_transfers = model.NewIntVar(0, 7, "excess_transfers")
    model.Add(excess_transfers >= transfer_count - free_transfers)
    model.Add(excess_transfers <= transfer_count)

    objective_terms = [
        _score_units(
            asset,
            projections[asset.asset_id],
            strategy_mode,
            custom_weights,
        )
        * decision_vars[asset.asset_id]
        for asset in candidates
    ]
    if chip_action not in {"wildcard", "limitless"}:
        objective_terms.append(
            -_score_units_from_float(
                penalty_points * weights_for(strategy_mode, custom_weights)["expected"]
            )
            * excess_transfers
        )
    model.Maximize(sum(objective_terms))

    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.max_time_in_seconds = 0.2

    selected_lineups: list[tuple[str, ...]] = []
    seen: set[tuple[str, ...]] = set()
    for _ in range(max_options):
        status = solver.Solve(model)
        if status not in {cp_model.OPTIMAL, cp_model.FEASIBLE}:
            break
        selected = tuple(
            sorted(
                asset_id
                for asset_id, decision_var in decision_vars.items()
                if solver.Value(decision_var) == 1
            )
        )
        if len(selected) != 7 or selected in seen:
            break
        selected_lineups.append(selected)
        seen.add(selected)
        model.Add(sum(decision_vars[asset_id] for asset_id in selected) <= 6)

    return selected_lineups


def _load_cp_model() -> Any | None:
    try:
        return cast(Any, import_module("ortools.sat.python.cp_model"))
    except ImportError:
        return None


def _score_units(
    asset: FantasyAsset,
    projection: Projection,
    strategy_mode: StrategyMode,
    custom_weights: dict[str, float],
) -> int:
    weights = weights_for(strategy_mode, custom_weights)
    expected = projection.expected_points
    risk = projection.risk_score
    floor = expected * (0.72 - risk * 0.12)
    ceiling = expected * (1.15 - risk * 0.10)
    differential = 1.0 if asset.asset_id.endswith(("foxtrot", "juliet", "four")) else 0.0
    budget_growth = projection.projected_price_delta_millions or 0
    score = (
        expected * weights["expected"]
        + floor * weights["floor"]
        + ceiling * weights["ceiling"]
        - risk * (20 / 7) * weights["riskPenalty"]
        + budget_growth * 10 * weights["budgetGrowth"]
        + differential * weights["differential"]
    )
    return _score_units_from_float(score)


def _score_units_from_float(value: float) -> int:
    return int(round(value * 100))


def _money_units(value: float) -> int:
    return int(round(value * 100))


def _var_name(asset_id: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in asset_id)
