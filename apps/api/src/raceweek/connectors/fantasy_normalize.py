from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

from raceweek.connectors.fantasy_readonly import FantasyReadOnlySnapshot
from raceweek.connectors.jolpica_normalize import JolpicaSeasonContext
from raceweek.connectors.manual_utils import default_chips
from raceweek.core.models import (
    ChipState,
    FantasyAsset,
    FantasyAssetScore,
    FantasyTeamSnapshot,
    TeamAsset,
    utc_now,
)
from raceweek.core.rules import InvalidLineup, validate_lineup

TEAM_COLORS: dict[str, str] = {
    "alpine": "#2293D1",
    "aston martin": "#006F62",
    "audi": "#9B0000",
    "cadillac": "#D4AF37",
    "ferrari": "#E8002D",
    "haas": "#B6BABD",
    "kick sauber": "#00E701",
    "mclaren": "#FF8000",
    "mercedes": "#27F4D2",
    "racing bulls": "#6692FF",
    "red bull": "#3671C6",
    "williams": "#64C4FF",
}


@dataclass(frozen=True)
class FantasyGameNormalization:
    assets: list[FantasyAsset]
    scores: list[FantasyAssetScore]
    teams: list[FantasyTeamSnapshot]


def normalize_game_snapshot(
    snapshot: FantasyReadOnlySnapshot,
    *,
    event_id: str,
    source_snapshot_id: str,
    slot: int | None = None,
) -> FantasyGameNormalization:
    stat_by_id = {_external_id(row): row for row in snapshot.live_stats if _external_id(row)}
    assets = [
        _player_asset(row, stat_by_id.get(_external_id(row)), source_snapshot_id)
        for row in snapshot.players
    ]
    assets.extend(_constructor_asset(row, source_snapshot_id) for row in snapshot.teams)
    assets = [asset for asset in assets if asset.display_name]
    scores = [
        FantasyAssetScore(
            asset_id=asset.asset_id,
            event_id=event_id,
            fantasy_points=asset.fantasy_points,
            ownership_pct=asset.ownership_pct,
            selected_by_pct=asset.selected_by_pct,
            captured_at=utc_now(),
            source_snapshot_id=source_snapshot_id,
        )
        for asset in assets
        if asset.fantasy_points is not None
    ]
    teams = _picked_teams(snapshot.picked_teams, assets, event_id, source_snapshot_id, slot)
    return FantasyGameNormalization(assets=assets, scores=scores, teams=teams)


def derive_public_history_scores(
    context: JolpicaSeasonContext,
    market_assets: list[FantasyAsset],
    *,
    event_id: str,
    source_snapshot_id: str,
    through_round: int | None,
) -> tuple[list[FantasyAsset], list[FantasyAssetScore]]:
    driver_points: dict[str, float] = {}
    constructor_points: dict[str, float] = {}
    cutoff = through_round or _latest_round(context)

    standings_round = _latest_standings_round(context, cutoff)
    if standings_round is not None:
        for standing in context.driver_standings:
            if standing.round_number == standings_round:
                key = _match_key(standing.driver_id or standing.driver_name)
                driver_points[key] = float(standing.points) + standing.wins * 5
        for standing in context.constructor_standings:
            if standing.round_number == standings_round:
                key = _match_key(standing.constructor_id or standing.constructor_name)
                constructor_points[key] = float(standing.points) + standing.wins * 5

    if not driver_points:
        for result in [*context.race_results, *context.sprint_results]:
            if result.round_number <= cutoff:
                key = _match_key(result.driver_id or result.driver_name)
                driver_points[key] = driver_points.get(key, 0) + float(result.points or 0)
                constructor_key = _match_key(result.constructor_id or result.constructor_name)
                constructor_points[constructor_key] = (
                    constructor_points.get(constructor_key, 0) + float(result.points or 0)
                )

    updated_assets: list[FantasyAsset] = []
    scores: list[FantasyAssetScore] = []
    for asset in market_assets:
        points = _asset_history_points(asset, driver_points, constructor_points)
        updated = asset.model_copy(
            update={
                "fantasy_points": points,
                "points_per_million": round(points / max(asset.price_millions, 1), 2),
                "source_snapshot_id": asset.source_snapshot_id,
            }
        )
        updated_assets.append(updated)
        scores.append(
            FantasyAssetScore(
                asset_id=asset.asset_id,
                event_id=event_id,
                fantasy_points=points,
                ownership_pct=asset.ownership_pct,
                selected_by_pct=asset.selected_by_pct,
                captured_at=utc_now(),
                source_snapshot_id=source_snapshot_id,
            )
        )
    return updated_assets, scores


def _player_asset(
    row: dict[str, Any],
    stat: dict[str, Any] | None,
    source_snapshot_id: str,
) -> FantasyAsset:
    external_id = _external_id(row)
    name = _name(row)
    constructor = _constructor_name(row)
    points = _number(_first(stat or {}, ["points", "fantasy_points", "total_points"]))
    price = _price(row)
    ownership = _number(_first(stat or row, ["ownership", "selected_by", "selected_by_pct"]))
    return FantasyAsset(
        asset_id=_asset_id("driver", external_id or name),
        asset_type="driver",
        display_name=name,
        external_id=external_id,
        short_name=_short_name(row, name),
        abbreviation=_abbreviation(row, name),
        constructor_name=constructor,
        team_color_hex=_team_color(row, constructor),
        price_millions=price,
        fantasy_points=points,
        ownership_pct=ownership,
        selected_by_pct=ownership,
        points_per_million=round(points / max(price, 1), 2) if points is not None else None,
        source_snapshot_id=source_snapshot_id,
    )


def _constructor_asset(row: dict[str, Any], source_snapshot_id: str) -> FantasyAsset:
    external_id = _external_id(row)
    name = _name(row)
    points = _number(_first(row, ["points", "fantasy_points", "total_points"]))
    price = _price(row)
    return FantasyAsset(
        asset_id=_asset_id("constructor", external_id or name),
        asset_type="constructor",
        display_name=name,
        external_id=external_id,
        short_name=_short_name(row, name),
        abbreviation=_abbreviation(row, name),
        constructor_name=name,
        team_color_hex=_team_color(row, name),
        price_millions=price,
        fantasy_points=points,
        ownership_pct=_number(_first(row, ["ownership", "selected_by", "selected_by_pct"])),
        selected_by_pct=_number(_first(row, ["ownership", "selected_by", "selected_by_pct"])),
        points_per_million=round(points / max(price, 1), 2) if points is not None else None,
        source_snapshot_id=source_snapshot_id,
    )


def _picked_teams(
    rows: list[dict[str, Any]],
    assets: list[FantasyAsset],
    event_id: str,
    source_snapshot_id: str,
    requested_slot: int | None,
) -> list[FantasyTeamSnapshot]:
    by_external = {asset.external_id: asset for asset in assets if asset.external_id}
    by_asset_id = {asset.asset_id: asset for asset in assets}
    teams: list[FantasyTeamSnapshot] = []
    for index, row in enumerate(rows, start=1):
        slot = _int(_first(row, ["slot", "team_slot"])) or requested_slot or index
        if slot not in {1, 2, 3}:
            continue
        selected_assets = []
        for item in _selected_ids(row):
            asset = (
                by_asset_id.get(item)
                or by_external.get(item)
                or by_asset_id.get(_asset_id("driver", item))
            )
            if asset is not None:
                selected_assets.append(asset)
        if len(selected_assets) != 7:
            continue
        try:
            validation = validate_lineup(selected_assets, cost_cap_millions=_cost_cap(row))
        except InvalidLineup:
            continue
        teams.append(
            FantasyTeamSnapshot(
                team_snapshot_id=(
                    f"team_fantasy_slot_{slot}_"
                    f"{_hash_ids([a.asset_id for a in selected_assets])}"
                ),
                team_name=str(_first(row, ["team_name", "name"]) or f"Team {slot}"),
                event_id=event_id,
                cost_cap_millions=_cost_cap(row),
                budget_used_millions=validation.budget_used_millions,
                budget_remaining_millions=validation.budget_remaining_millions,
                free_transfers=_int(_first(row, ["free_transfers", "transfers"])) or 2,
                transfer_penalty_points=10,
                captured_at=utc_now(),
                source_snapshot_id=source_snapshot_id,
                slot=slot,
                assets=[
                    TeamAsset(asset_id=asset.asset_id, asset_type=asset.asset_type)
                    for asset in selected_assets
                ],
                chips=[ChipState.model_validate(chip) for chip in default_chips()],
            )
        )
    return teams


def _selected_ids(row: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ["asset_ids", "assetIds", "player_ids", "playerIds", "players", "drivers"]:
        values.extend(_ids_from_value(row.get(key)))
    for key in ["constructor_ids", "constructorIds", "teams", "constructors"]:
        values.extend(_ids_from_value(row.get(key)))
    return values


def _ids_from_value(value: object) -> list[str]:
    if isinstance(value, str):
        return [part.strip() for part in re.split(r"[;,|]", value) if part.strip()]
    if isinstance(value, list):
        values: list[str] = []
        for item in value:
            if isinstance(item, dict):
                item_id = _external_id(item) or _str(_first(item, ["asset_id", "assetId"]))
                if item_id:
                    values.append(item_id)
            elif item is not None:
                values.append(str(item))
        return values
    return []


def _asset_history_points(
    asset: FantasyAsset,
    driver_points: dict[str, float],
    constructor_points: dict[str, float],
) -> float:
    keys = {
        _match_key(asset.external_id),
        _match_key(asset.display_name),
        _match_key(asset.short_name),
    }
    if asset.asset_type == "constructor":
        keys.add(_match_key(asset.constructor_name))
        return round(max(constructor_points.get(key, 0) for key in keys), 2)
    return round(max(driver_points.get(key, 0) for key in keys), 2)


def _latest_round(context: JolpicaSeasonContext) -> int:
    rounds = [race.round_number for race in context.races]
    return max(rounds, default=1)


def _latest_standings_round(context: JolpicaSeasonContext, cutoff: int) -> int | None:
    rounds = [
        standing.round_number
        for standing in [*context.driver_standings, *context.constructor_standings]
        if standing.round_number is not None and standing.round_number <= cutoff
    ]
    return max(rounds, default=None)


def _external_id(row: dict[str, Any]) -> str | None:
    return _str(
        _first(row, ["id", "player_id", "playerId", "driver_id", "constructor_id", "team_id"])
    )


def _name(row: dict[str, Any]) -> str:
    value = _first(row, ["display_name", "displayName", "full_name", "fullName", "name"])
    if value:
        return str(value)
    first = _str(_first(row, ["first_name", "firstName", "givenName"]))
    last = _str(_first(row, ["last_name", "lastName", "familyName"]))
    return " ".join(part for part in [first, last] if part) or "Unknown"


def _constructor_name(row: dict[str, Any]) -> str | None:
    value = _first(
        row,
        ["constructor_name", "constructorName", "team_name", "teamName", "team", "constructor"],
    )
    return _str(value)


def _short_name(row: dict[str, Any], name: str) -> str:
    return _str(_first(row, ["short_name", "shortName", "last_name", "lastName"])) or name


def _abbreviation(row: dict[str, Any], name: str) -> str:
    configured = _str(_first(row, ["abbreviation", "abbr", "tla", "code"]))
    if configured:
        return configured.upper()[:4]
    parts = name.split()
    token = parts[-1] if parts else name
    return re.sub(r"[^A-Za-z]", "", token).upper()[:3] or "UNK"


def _team_color(row: dict[str, Any], constructor_name: str | None) -> str | None:
    configured = _str(_first(row, ["team_color", "teamColor", "colour", "color", "colorHex"]))
    if configured:
        return configured if configured.startswith("#") else f"#{configured}"
    normalized = (constructor_name or "").lower()
    match = next((color for name, color in TEAM_COLORS.items() if name in normalized), None)
    return match


def _price(row: dict[str, Any]) -> float:
    value = _number(
        _first(row, ["price", "current_price", "currentPrice", "price_millions", "value", "cost"])
    )
    if value is None:
        return 0
    if value > 1000:
        return round(value / 1_000_000, 2)
    if value > 100:
        return round(value / 10, 2)
    return value


def _cost_cap(row: dict[str, Any]) -> float:
    return _number(_first(row, ["cost_cap", "costCap", "budget_cap", "budgetCap"])) or 100


def _first(row: dict[str, Any], keys: list[str]) -> object | None:
    return next((row[key] for key in keys if key in row and row[key] not in {None, ""}), None)


def _number(value: object) -> float | None:
    if value in {None, ""}:
        return None
    try:
        text = str(value).replace("%", "").strip()
        parsed = float(text)
    except ValueError:
        return None
    if parsed <= 1 and "%" not in str(value):
        return round(parsed * 100, 2)
    return round(parsed, 2)


def _int(value: object) -> int | None:
    try:
        return None if value in {None, ""} else int(str(value))
    except ValueError:
        return None


def _str(value: object) -> str | None:
    return None if value in {None, ""} else str(value)


def _asset_id(kind: str, value: str | None) -> str:
    return f"asset_{kind}_{_slug(value or 'unknown')}"


def _slug(value: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", value.lower())).strip("_")


def _match_key(value: str | None) -> str:
    return _slug(value or "")


def _hash_ids(asset_ids: list[str]) -> str:
    raw = "|".join(sorted(asset_ids))
    return hashlib.sha256(raw.encode()).hexdigest()[:12]
