import pytest

from raceweek.core.models import ChipState, FantasyAsset, FantasyTeamSnapshot, TeamAsset
from raceweek.core.rules import (
    InvalidLineup,
    InvalidLineupTransition,
    apply_autopilot_boost,
    apply_no_negative,
    calculate_net_transfers,
    calculate_transfer_penalty,
    validate_final_fix,
    validate_lineup,
)


def asset(asset_id: str, asset_type: str, price: float) -> FantasyAsset:
    return FantasyAsset(
        assetId=asset_id,
        assetType=asset_type,
        displayName=asset_id.replace("_", " ").title(),
        priceMillions=price,
        fantasyPoints=10,
    )


def legal_assets() -> list[FantasyAsset]:
    return [
        asset("d1", "driver", 20),
        asset("d2", "driver", 18),
        asset("d3", "driver", 15),
        asset("d4", "driver", 10),
        asset("d5", "driver", 7),
        asset("c1", "constructor", 15),
        asset("c2", "constructor", 10),
    ]


def test_legal_lineup_with_five_drivers_two_constructors_passes() -> None:
    result = validate_lineup(legal_assets(), cost_cap_millions=100)

    assert result.budget_used_millions == 95
    assert result.budget_remaining_millions == 5


def test_duplicate_asset_fails() -> None:
    lineup = legal_assets()
    lineup[-1] = lineup[0]

    with pytest.raises(InvalidLineup, match="duplicate"):
        validate_lineup(lineup, cost_cap_millions=100)


def test_over_budget_lineup_fails_and_limitless_ignores_budget() -> None:
    lineup = legal_assets()

    with pytest.raises(InvalidLineup, match="budget"):
        validate_lineup(lineup, cost_cap_millions=80)

    result = validate_lineup(lineup, cost_cap_millions=80, chip_action="limitless")
    assert result.budget_remaining_millions == -15


def test_transfer_count_ignores_order_and_rejects_size_changes() -> None:
    assert calculate_net_transfers({"a", "b", "c"}, {"c", "b", "a"}) == 0
    assert calculate_net_transfers({"a", "b", "c"}, {"a", "b", "d"}) == 1

    with pytest.raises(InvalidLineupTransition):
        calculate_net_transfers({"a", "b"}, {"a", "b", "c"})


def test_transfer_penalty_honors_free_transfers_and_chips() -> None:
    assert calculate_transfer_penalty(4, free_transfers=2, penalty_points=10) == 20
    assert (
        calculate_transfer_penalty(
            4,
            free_transfers=2,
            penalty_points=10,
            chip_action="wildcard",
        )
        == 0
    )
    assert (
        calculate_transfer_penalty(
            4,
            free_transfers=2,
            penalty_points=10,
            chip_action="limitless",
        )
        == 0
    )


def test_no_negative_floors_negative_scores() -> None:
    assert apply_no_negative({"d1": 12, "d2": -8}, active=False) == {"d1": 12, "d2": -8}
    assert apply_no_negative({"d1": 12, "d2": -8}, active=True) == {"d1": 12, "d2": 0}


def test_autopilot_assigns_boost_to_top_driver() -> None:
    scores = {"d1": 8, "d2": 31, "d3": 14, "c1": 40}
    boosted = apply_autopilot_boost(scores, driver_asset_ids={"d1", "d2", "d3"})

    assert boosted["d2"] == 62
    assert boosted["c1"] == 40


def test_final_fix_allows_one_late_driver_change_only() -> None:
    previous = {"d1", "d2", "d3", "d4", "d5", "c1", "c2"}
    proposed = {"d1", "d2", "d3", "d4", "d6", "c1", "c2"}

    validate_final_fix(previous, proposed, driver_asset_ids={"d1", "d2", "d3", "d4", "d5", "d6"})

    with pytest.raises(InvalidLineupTransition):
        validate_final_fix(
            previous,
            {"d1", "d2", "d3", "d6", "d7", "c1", "c2"},
            {"d1", "d2", "d3", "d4", "d5", "d6", "d7"},
        )


def test_team_snapshot_budget_matches_assets() -> None:
    team = FantasyTeamSnapshot(
        teamSnapshotId="team_test",
        teamName="Test Team",
        eventId="event_1",
        costCapMillions=100,
        budgetUsedMillions=95,
        budgetRemainingMillions=5,
        freeTransfers=2,
        assets=[
            TeamAsset(assetId="d1", assetType="driver"),
            TeamAsset(assetId="d2", assetType="driver"),
            TeamAsset(assetId="d3", assetType="driver"),
            TeamAsset(assetId="d4", assetType="driver"),
            TeamAsset(assetId="d5", assetType="driver"),
            TeamAsset(assetId="c1", assetType="constructor"),
            TeamAsset(assetId="c2", assetType="constructor"),
        ],
        chips=[ChipState(chipName="wildcard", status="available")],
        capturedAt="2026-06-05T00:00:00Z",
    )

    assert team.asset_ids == {"d1", "d2", "d3", "d4", "d5", "c1", "c2"}
