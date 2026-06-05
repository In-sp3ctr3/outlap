from __future__ import annotations

from collections import Counter

from raceweek.core.models import FantasyAsset, LineupValidation


class InvalidLineup(ValueError):
    pass


class InvalidLineupTransition(ValueError):
    pass


def validate_lineup(
    lineup: list[FantasyAsset],
    *,
    cost_cap_millions: float,
    chip_action: str | None = None,
) -> LineupValidation:
    asset_ids = [asset.asset_id for asset in lineup]
    duplicates = [asset_id for asset_id, count in Counter(asset_ids).items() if count > 1]
    if duplicates:
        raise InvalidLineup(f"lineup contains duplicate asset IDs: {', '.join(sorted(duplicates))}")

    driver_count = sum(1 for asset in lineup if asset.asset_type == "driver")
    constructor_count = sum(1 for asset in lineup if asset.asset_type == "constructor")
    if driver_count != 5:
        raise InvalidLineup(f"lineup must contain exactly 5 drivers, got {driver_count}")
    if constructor_count != 2:
        raise InvalidLineup(f"lineup must contain exactly 2 constructors, got {constructor_count}")

    budget_used = round(sum(asset.price_millions for asset in lineup), 2)
    budget_remaining = round(cost_cap_millions - budget_used, 2)
    if budget_remaining < -0.0001 and chip_action != "limitless":
        raise InvalidLineup(
            f"lineup exceeds budget cap by {abs(budget_remaining):.1f}M without Limitless"
        )

    return LineupValidation(
        budget_used_millions=budget_used,
        budget_remaining_millions=budget_remaining,
        driver_count=driver_count,
        constructor_count=constructor_count,
    )


def calculate_net_transfers(previous_asset_ids: set[str], proposed_asset_ids: set[str]) -> int:
    removed = previous_asset_ids - proposed_asset_ids
    added = proposed_asset_ids - previous_asset_ids
    if len(removed) != len(added):
        raise InvalidLineupTransition("lineup size changed unexpectedly")
    return len(added)


def calculate_transfer_penalty(
    net_transfers: int,
    *,
    free_transfers: int,
    penalty_points: float,
    chip_action: str | None = None,
) -> float:
    if chip_action in {"wildcard", "limitless"}:
        return 0
    return max(0, net_transfers - free_transfers) * penalty_points


def apply_no_negative(scores: dict[str, float], *, active: bool) -> dict[str, float]:
    if not active:
        return dict(scores)
    return {asset_id: max(0, score) for asset_id, score in scores.items()}


def apply_autopilot_boost(
    scores: dict[str, float],
    *,
    driver_asset_ids: set[str],
    multiplier: float = 2,
) -> dict[str, float]:
    boosted = dict(scores)
    eligible = {
        asset_id: score
        for asset_id, score in scores.items()
        if asset_id in driver_asset_ids
    }
    if not eligible:
        return boosted
    top_driver = sorted(eligible.items(), key=lambda item: (-item[1], item[0]))[0][0]
    boosted[top_driver] = boosted[top_driver] * multiplier
    return boosted


def validate_final_fix(
    previous_asset_ids: set[str],
    proposed_asset_ids: set[str],
    driver_asset_ids: set[str],
) -> None:
    removed = previous_asset_ids - proposed_asset_ids
    added = proposed_asset_ids - previous_asset_ids
    if len(removed) != 1 or len(added) != 1:
        raise InvalidLineupTransition("Final Fix allows exactly one late driver change")
    if not removed <= driver_asset_ids or not added <= driver_asset_ids:
        raise InvalidLineupTransition("Final Fix can only change one driver")
