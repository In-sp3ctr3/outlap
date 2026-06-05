from datetime import UTC, datetime

from raceweek.core.models import (
    FantasyAsset,
    FantasyTeamSnapshot,
    Projection,
    RecommendationRunResult,
    StrategyMode,
    TeamAsset,
)
from raceweek.core.optimizer import optimize_recommendations


def test_custom_weights_change_ranking_and_request_fingerprint() -> None:
    team, assets, projections = _custom_weight_fixture()
    balanced = _optimize_custom_fixture(team, assets, projections, strategy_mode="balanced")
    custom = _optimize_custom_fixture(
        team,
        assets,
        projections,
        strategy_mode="custom",
        custom_weights={
            "expected": 0,
            "floor": 0,
            "ceiling": 0,
            "riskPenalty": 1,
            "budgetGrowth": 0,
            "differential": 0,
        },
        idempotency_key="risk-first",
    )
    repeated = _optimize_custom_fixture(
        team,
        assets,
        projections,
        strategy_mode="custom",
        custom_weights=custom.request_context.custom_weights,
        idempotency_key="risk-first",
    )

    assert "driver_high_expected" in balanced.options[0].selected_asset_ids
    assert "driver_low_risk" in custom.options[0].selected_asset_ids
    assert custom.request_context.custom_weights["riskPenalty"] == 1
    assert custom.request_context.idempotency_key_hash is not None
    assert custom.request_fingerprint != balanced.request_fingerprint
    assert custom.recommendation_run_id == repeated.recommendation_run_id


def _optimize_custom_fixture(
    team: FantasyTeamSnapshot,
    assets: list[FantasyAsset],
    projections: list[Projection],
    *,
    strategy_mode: StrategyMode,
    custom_weights: dict[str, float] | None = None,
    idempotency_key: str | None = None,
) -> RecommendationRunResult:
    return optimize_recommendations(
        team=team,
        assets=assets,
        projections=projections,
        event_id="event_custom",
        strategy_mode=strategy_mode,
        locked_asset_ids=[],
        banned_asset_ids=[],
        allowed_chips=[],
        custom_weights=custom_weights or {},
        idempotency_key=idempotency_key,
        max_options=1,
        projection_run_id="projrun_custom",
        source_snapshot_ids=["snapshot_custom"],
    )


def _custom_weight_fixture() -> tuple[
    FantasyTeamSnapshot,
    list[FantasyAsset],
    list[Projection],
]:
    assets = [
        _asset("driver_alpha", "driver", 10),
        _asset("driver_bravo", "driver", 10),
        _asset("driver_charlie", "driver", 10),
        _asset("driver_delta", "driver", 10),
        _asset("driver_high_expected", "driver", 10),
        _asset("driver_low_risk", "driver", 10),
        _asset("constructor_one", "constructor", 10),
        _asset("constructor_two", "constructor", 10),
    ]
    projections = [
        _projection("driver_alpha", expected_points=8, risk_score=0.2),
        _projection("driver_bravo", expected_points=8, risk_score=0.2),
        _projection("driver_charlie", expected_points=8, risk_score=0.2),
        _projection("driver_delta", expected_points=8, risk_score=0.2),
        _projection("driver_high_expected", expected_points=20, risk_score=0.95),
        _projection("driver_low_risk", expected_points=12, risk_score=0.05),
        _projection("constructor_one", expected_points=9, risk_score=0.2),
        _projection("constructor_two", expected_points=9, risk_score=0.2),
    ]
    team = FantasyTeamSnapshot(
        team_snapshot_id="team_custom",
        team_name="Custom Weights",
        event_id="event_custom",
        cost_cap_millions=100,
        budget_used_millions=70,
        budget_remaining_millions=30,
        free_transfers=1,
        transfer_penalty_points=10,
        assets=[
            TeamAsset(asset_id="driver_alpha", asset_type="driver"),
            TeamAsset(asset_id="driver_bravo", asset_type="driver"),
            TeamAsset(asset_id="driver_charlie", asset_type="driver"),
            TeamAsset(asset_id="driver_delta", asset_type="driver"),
            TeamAsset(asset_id="driver_high_expected", asset_type="driver"),
            TeamAsset(asset_id="constructor_one", asset_type="constructor"),
            TeamAsset(asset_id="constructor_two", asset_type="constructor"),
        ],
        chips=[],
        captured_at=datetime(2026, 6, 5, tzinfo=UTC),
    )
    return team, assets, projections


def _asset(asset_id: str, asset_type: str, price_millions: float) -> FantasyAsset:
    return FantasyAsset(
        asset_id=asset_id,
        asset_type=asset_type,
        display_name=asset_id,
        price_millions=price_millions,
    )


def _projection(
    asset_id: str,
    *,
    expected_points: float,
    risk_score: float,
) -> Projection:
    return Projection(
        asset_id=asset_id,
        expected_points=expected_points,
        floor_points=expected_points * 0.7,
        ceiling_points=expected_points * 1.2,
        confidence=0.9,
        risk_score=risk_score,
    )
