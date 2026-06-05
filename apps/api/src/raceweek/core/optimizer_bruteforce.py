from __future__ import annotations

from itertools import combinations

from raceweek.core.models import FantasyAsset
from raceweek.core.rules import InvalidLineup, validate_lineup


def solve_lineups_with_bruteforce(
    *,
    assets: list[FantasyAsset],
    locked_asset_ids: set[str],
    cost_cap_millions: float,
    chip_action: str | None,
) -> list[tuple[str, ...]]:
    drivers = [asset for asset in assets if asset.asset_type == "driver"]
    constructors = [asset for asset in assets if asset.asset_type == "constructor"]
    locked_drivers = {
        asset.asset_id for asset in drivers if asset.asset_id in locked_asset_ids
    }
    locked_constructors = {
        asset.asset_id for asset in constructors if asset.asset_id in locked_asset_ids
    }
    lineups: list[tuple[str, ...]] = []

    for driver_combo in combinations(drivers, 5):
        driver_ids = {asset.asset_id for asset in driver_combo}
        if not locked_drivers <= driver_ids:
            continue
        for constructor_combo in combinations(constructors, 2):
            constructor_ids = {asset.asset_id for asset in constructor_combo}
            if not locked_constructors <= constructor_ids:
                continue
            lineup = [*driver_combo, *constructor_combo]
            try:
                validate_lineup(
                    lineup,
                    cost_cap_millions=cost_cap_millions,
                    chip_action=chip_action,
                )
            except InvalidLineup:
                continue
            lineups.append(tuple(sorted(asset.asset_id for asset in lineup)))

    return lineups
