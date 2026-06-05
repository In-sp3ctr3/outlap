import pytest

from raceweek.core.models import RecommendationRunResult, StrategyMode
from raceweek.core.optimizer import optimize_recommendations
from raceweek.core.projections import run_projection
from raceweek.storage.demo import seed_demo_state


def _run_optimizer(
    *,
    strategy_mode: StrategyMode = "balanced",
    locked_asset_ids: list[str] | None = None,
    banned_asset_ids: list[str] | None = None,
    allowed_chips: list[str] | None = None,
    custom_weights: dict[str, float] | None = None,
    idempotency_key: str | None = None,
    max_options: int = 5,
) -> RecommendationRunResult:
    state = seed_demo_state()
    projection_run = run_projection(state.assets, event_id=state.current_event_id)
    return optimize_recommendations(
        team=state.team,
        assets=state.assets,
        projections=projection_run.projections,
        event_id=state.current_event_id,
        strategy_mode=strategy_mode,
        locked_asset_ids=locked_asset_ids or [],
        banned_asset_ids=banned_asset_ids or [],
        allowed_chips=allowed_chips or [],
        custom_weights=custom_weights or {},
        idempotency_key=idempotency_key,
        max_options=max_options,
        projection_run_id=projection_run.projection_run_id,
        source_snapshot_ids=projection_run.source_snapshot_ids,
    )


def test_optimizer_returns_legal_deterministic_options_with_provenance() -> None:
    state = seed_demo_state()
    projection_run = run_projection(state.assets, event_id=state.current_event_id)

    first = optimize_recommendations(
        team=state.team,
        assets=state.assets,
        projections=projection_run.projections,
        event_id=state.current_event_id,
        strategy_mode="balanced",
        locked_asset_ids=[],
        banned_asset_ids=[],
        allowed_chips=[],
        max_options=5,
        projection_run_id=projection_run.projection_run_id,
        source_snapshot_ids=projection_run.source_snapshot_ids,
    )
    second = optimize_recommendations(
        team=state.team,
        assets=state.assets,
        projections=projection_run.projections,
        event_id=state.current_event_id,
        strategy_mode="balanced",
        locked_asset_ids=[],
        banned_asset_ids=[],
        allowed_chips=[],
        max_options=5,
        projection_run_id=projection_run.projection_run_id,
        source_snapshot_ids=projection_run.source_snapshot_ids,
    )

    assert [option.model_dump() for option in first.options] == [
        option.model_dump() for option in second.options
    ]
    assert first.options
    assert first.options[0].expected_net_points >= first.options[-1].expected_net_points
    assert first.options[0].source_snapshot_ids
    assert first.options[0].projection_run_id == projection_run.projection_run_id
    assert first.options[0].ruleset_version == "fantasy_demo_2026_v1"
    assert first.options[0].optimizer_version == "ortools_cp_sat_v1"


def test_optimizer_honors_locked_and_banned_assets() -> None:
    result = _run_optimizer(
        strategy_mode="aggressive",
        locked_asset_ids=["asset_driver_echo"],
        banned_asset_ids=["asset_driver_foxtrot"],
    )

    assert result.options
    for option in result.options:
        selected = option.selected_asset_ids
        assert "asset_driver_echo" in selected
        assert "asset_driver_foxtrot" not in selected


def test_wildcard_zeroes_transfer_penalty_and_limitless_can_exceed_budget() -> None:
    state = seed_demo_state()
    wildcard = _run_optimizer(
        strategy_mode="chip_optimized",
        allowed_chips=["wildcard"],
        max_options=10,
    )
    limitless = _run_optimizer(
        strategy_mode="chip_optimized",
        allowed_chips=["limitless"],
        max_options=10,
    )

    assert any(
        option.chip_action == "wildcard" and option.transfer_penalty_points == 0
        for option in wildcard.options
    )
    assert any(
        option.chip_action == "limitless"
        and option.budget_used_millions > state.team.cost_cap_millions
        for option in limitless.options
    )


def test_chip_optimized_compares_no_chip_and_chip_scenarios() -> None:
    result = _run_optimizer(
        strategy_mode="chip_optimized",
        allowed_chips=["wildcard"],
        max_options=10,
    )

    assert {None, "wildcard"} <= {option.chip_action for option in result.options}


def test_all_strategy_modes_return_ranked_options() -> None:
    strategy_modes: list[StrategyMode] = [
        "safe",
        "balanced",
        "aggressive",
        "budget_builder",
        "differential",
        "chip_optimized",
    ]
    for strategy_mode in strategy_modes:
        result = _run_optimizer(strategy_mode=strategy_mode, max_options=3)

        assert len(result.options) == 3
        assert [option.rank for option in result.options] == [1, 2, 3]
        assert all(option.strategy_mode == strategy_mode for option in result.options)


def test_optimizer_falls_back_to_bruteforce_when_solver_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("raceweek.core.optimizer.solve_lineups_with_ortools", lambda **_: [])

    result = _run_optimizer(strategy_mode="balanced", max_options=3)

    assert result.options
    assert all(option.optimizer_version == "bruteforce_demo_v1" for option in result.options)


def test_impossible_optimizer_constraints_return_useful_warning() -> None:
    result = _run_optimizer(
        strategy_mode="safe",
        locked_asset_ids=[
            "asset_driver_alpha",
            "asset_driver_bravo",
            "asset_driver_charlie",
            "asset_driver_delta",
            "asset_driver_echo",
            "asset_driver_foxtrot",
        ],
        max_options=3,
    )

    assert result.options == []
    assert "No legal lineup matched the selected constraints." in result.warnings
