from __future__ import annotations

from raceweek.core.models import FantasyAsset, Projection
from raceweek.core.rules import apply_autopilot_boost, apply_no_negative


def simulate_chip_scores(
    *,
    lineup: list[FantasyAsset],
    projections: dict[str, Projection],
    team_asset_boosts: dict[str, float],
    chip_action: str | None,
) -> dict[str, float]:
    scores = {asset.asset_id: projections[asset.asset_id].expected_points for asset in lineup}
    driver_ids = {asset.asset_id for asset in lineup if asset.asset_type == "driver"}
    triple_boost_asset_id = _triple_boost_asset_id(scores, driver_ids, chip_action)

    boosted = {}
    for asset_id, score in scores.items():
        if asset_id == triple_boost_asset_id:
            boosted[asset_id] = score * 3
            continue
        boosted[asset_id] = score * max(1, team_asset_boosts.get(asset_id, 1))

    if chip_action == "autopilot":
        boosted = apply_autopilot_boost(boosted, driver_asset_ids=driver_ids)
    if chip_action == "no_negative":
        boosted = apply_no_negative(boosted, active=True)
    return boosted


def _triple_boost_asset_id(
    scores: dict[str, float],
    driver_ids: set[str],
    chip_action: str | None,
) -> str | None:
    if chip_action != "3x_boost":
        return None
    eligible = {
        asset_id: score for asset_id, score in scores.items() if asset_id in driver_ids
    }
    if not eligible:
        return None
    return sorted(eligible.items(), key=lambda item: (-item[1], item[0]))[0][0]
