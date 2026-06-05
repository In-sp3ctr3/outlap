from datetime import UTC, datetime

from raceweek.core.models import (
    FantasyAsset,
    FantasyTeamSnapshot,
    Projection,
    RecommendationRunResult,
    TeamAsset,
)
from raceweek.core.optimizer import optimize_recommendations


def test_regular_boost_multiplier_changes_expected_gross_points() -> None:
    team, assets, projections = _chip_fixture(boosted_driver="driver_one")

    result = _run_chip_optimizer(team, assets, projections, chip_action=None)

    assert result.options[0].expected_gross_points == 50


def test_3x_boost_replaces_regular_boost_for_top_driver() -> None:
    team, assets, projections = _chip_fixture(boosted_driver="driver_one")

    result = _run_chip_optimizer(team, assets, projections, chip_action="3x_boost")

    assert result.options[0].chip_action == "3x_boost"
    assert result.options[0].expected_gross_points == 60


def test_autopilot_boosts_highest_projected_driver() -> None:
    team, assets, projections = _chip_fixture(driver_two_points=12)

    result = _run_chip_optimizer(team, assets, projections, chip_action="autopilot")

    assert result.options[0].chip_action == "autopilot"
    assert result.options[0].expected_gross_points == 59


def test_no_negative_floors_negative_expected_scores() -> None:
    team, assets, projections = _chip_fixture(driver_five_points=-5)

    regular = _run_chip_optimizer(team, assets, projections, chip_action=None)
    no_negative = _run_chip_optimizer(team, assets, projections, chip_action="no_negative")

    assert regular.options[0].expected_gross_points == 30
    assert no_negative.options[0].expected_gross_points == 35


def test_final_fix_allows_only_one_late_driver_change() -> None:
    team, assets, projections = _chip_fixture(include_extra_driver=True)

    result = _run_chip_optimizer(
        team,
        assets,
        projections,
        chip_action="final_fix",
        max_options=5,
    )

    assert result.options
    for option in result.options:
        removed = team.asset_ids - set(option.selected_asset_ids)
        added = set(option.selected_asset_ids) - team.asset_ids
        assert len(removed) == 1
        assert len(added) == 1
        assert all(asset_id.startswith("driver_") for asset_id in removed | added)


def _run_chip_optimizer(
    team: FantasyTeamSnapshot,
    assets: list[FantasyAsset],
    projections: list[Projection],
    *,
    chip_action: str | None,
    max_options: int = 1,
) -> RecommendationRunResult:
    return optimize_recommendations(
        team=team,
        assets=assets,
        projections=projections,
        event_id="event_chips",
        strategy_mode="balanced",
        locked_asset_ids=[],
        banned_asset_ids=[],
        allowed_chips=[chip_action] if chip_action else [],
        max_options=max_options,
        projection_run_id="projrun_chips",
        source_snapshot_ids=["snapshot_chips"],
    )


def _chip_fixture(
    *,
    boosted_driver: str | None = None,
    driver_two_points: float = 5,
    driver_five_points: float = 5,
    include_extra_driver: bool = False,
) -> tuple[FantasyTeamSnapshot, list[FantasyAsset], list[Projection]]:
    asset_ids = [
        "driver_one",
        "driver_two",
        "driver_three",
        "driver_four",
        "driver_five",
        "constructor_one",
        "constructor_two",
    ]
    if include_extra_driver:
        asset_ids.append("driver_six")
    assets = [
        _asset(asset_id, "constructor" if asset_id.startswith("constructor") else "driver")
        for asset_id in asset_ids
    ]
    points = {
        "driver_one": 10,
        "driver_two": driver_two_points,
        "driver_three": 5,
        "driver_four": 5,
        "driver_five": driver_five_points,
        "driver_six": 16,
        "constructor_one": 5,
        "constructor_two": 5,
    }
    projections = [
        Projection(
            asset_id=asset.asset_id,
            expected_points=points[asset.asset_id],
            confidence=0.9,
            risk_score=0.2,
        )
        for asset in assets
    ]
    team_assets = [
        TeamAsset(
            asset_id=asset_id,
            asset_type="constructor" if asset_id.startswith("constructor") else "driver",
            boost_multiplier=2 if asset_id == boosted_driver else 1,
        )
        for asset_id in asset_ids[:7]
    ]
    team = FantasyTeamSnapshot(
        team_snapshot_id="team_chips",
        team_name="Chip Team",
        event_id="event_chips",
        cost_cap_millions=100,
        budget_used_millions=70,
        budget_remaining_millions=30,
        free_transfers=1,
        transfer_penalty_points=10,
        assets=team_assets,
        chips=[],
        captured_at=datetime(2026, 6, 5, tzinfo=UTC),
    )
    return team, assets, projections


def _asset(asset_id: str, asset_type: str) -> FantasyAsset:
    return FantasyAsset(
        asset_id=asset_id,
        asset_type=asset_type,
        display_name=asset_id,
        price_millions=10,
    )
