from raceweek.core.optimizer import optimize_recommendations
from raceweek.core.projections import run_projection
from raceweek.storage.demo import seed_demo_state


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


def test_optimizer_honors_locked_and_banned_assets() -> None:
    state = seed_demo_state()
    projection_run = run_projection(state.assets, event_id=state.current_event_id)

    result = optimize_recommendations(
        team=state.team,
        assets=state.assets,
        projections=projection_run.projections,
        event_id=state.current_event_id,
        strategy_mode="aggressive",
        locked_asset_ids=["asset_driver_echo"],
        banned_asset_ids=["asset_driver_foxtrot"],
        allowed_chips=[],
        max_options=5,
        projection_run_id=projection_run.projection_run_id,
        source_snapshot_ids=projection_run.source_snapshot_ids,
    )

    assert result.options
    for option in result.options:
        selected = option.selected_asset_ids
        assert "asset_driver_echo" in selected
        assert "asset_driver_foxtrot" not in selected


def test_wildcard_zeroes_transfer_penalty_and_limitless_can_exceed_budget() -> None:
    state = seed_demo_state()
    projection_run = run_projection(state.assets, event_id=state.current_event_id)

    wildcard = optimize_recommendations(
        team=state.team,
        assets=state.assets,
        projections=projection_run.projections,
        event_id=state.current_event_id,
        strategy_mode="chip_optimized",
        locked_asset_ids=[],
        banned_asset_ids=[],
        allowed_chips=["wildcard"],
        max_options=10,
        projection_run_id=projection_run.projection_run_id,
        source_snapshot_ids=projection_run.source_snapshot_ids,
    )
    limitless = optimize_recommendations(
        team=state.team,
        assets=state.assets,
        projections=projection_run.projections,
        event_id=state.current_event_id,
        strategy_mode="chip_optimized",
        locked_asset_ids=[],
        banned_asset_ids=[],
        allowed_chips=["limitless"],
        max_options=10,
        projection_run_id=projection_run.projection_run_id,
        source_snapshot_ids=projection_run.source_snapshot_ids,
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
