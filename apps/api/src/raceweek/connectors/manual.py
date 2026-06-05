from __future__ import annotations

from pydantic import ValidationError

from raceweek.connectors.manual_types import (
    ASSET_FIELDS,
    CHIP_FIELDS,
    LEAGUE_FIELDS,
    MARKET_FIELDS,
    SCORE_FIELDS,
    SNAPSHOT_MANUAL_LEAGUE,
    SNAPSHOT_MANUAL_MARKET,
    SNAPSHOT_MANUAL_SCORES,
    SNAPSHOT_MANUAL_TEAM,
    TEAM_ASSET_FIELDS,
    TEAM_FIELDS,
    ManualImportError,
    ParsedLeagueImport,
    ParsedMarketImport,
    ParsedScoresImport,
    ParsedTeamImport,
)
from raceweek.connectors.manual_utils import (
    as_dict,
    default_chips,
    filter_list,
    filter_mapping,
    read_csv_rows,
    reject_duplicate_ids,
    required_float,
    required_int,
    required_str,
    split_asset_ids,
)
from raceweek.core.models import (
    FantasyAsset,
    FantasyAssetScore,
    FantasyTeamSnapshot,
    LineupValidation,
    utc_now,
)
from raceweek.core.rules import InvalidLineup, validate_lineup


def parse_team_import(
    payload: dict[str, object],
    market_assets: list[FantasyAsset],
) -> ParsedTeamImport:
    body = as_dict(payload)
    if body.get("format") == "csv":
        return _parse_team_csv(body, market_assets)

    filtered, warnings = filter_mapping(body, TEAM_FIELDS, "team")
    filtered["assets"], asset_warnings = filter_list(
        filtered.get("assets"),
        TEAM_ASSET_FIELDS,
        "team.assets",
    )
    warnings.extend(asset_warnings)
    filtered["chips"], chip_warnings = filter_list(
        filtered.get("chips"),
        CHIP_FIELDS,
        "team.chips",
    )
    warnings.extend(chip_warnings)
    team = _validate_team_model(filtered)
    warnings.extend(_validate_team_lineup(team, market_assets))
    snapshot_id = team.source_snapshot_id or SNAPSHOT_MANUAL_TEAM
    team = team.model_copy(update={"source_snapshot_id": snapshot_id})
    return ParsedTeamImport(team, snapshot_id, warnings, body)


def parse_market_import(payload: dict[str, object]) -> ParsedMarketImport:
    body = as_dict(payload)
    if body.get("format") == "csv":
        return _parse_market_csv(body)

    filtered, warnings = filter_mapping(body, MARKET_FIELDS, "market")
    event_id = required_str(filtered, "eventId")
    assets_payload, asset_warnings = filter_list(
        filtered.get("assets"),
        ASSET_FIELDS,
        "market.assets",
    )
    warnings.extend(asset_warnings)
    assets = [_validate_asset_model(asset) for asset in assets_payload]
    snapshot_id = str(filtered.get("sourceSnapshotId") or SNAPSHOT_MANUAL_MARKET)
    assets = [_asset_with_snapshot(asset, snapshot_id) for asset in assets]
    reject_duplicate_ids([asset.asset_id for asset in assets], "market asset")
    return ParsedMarketImport(event_id, assets, snapshot_id, warnings, body)


def parse_league_import(payload: dict[str, object]) -> ParsedLeagueImport:
    body = as_dict(payload)
    if body.get("format") == "csv":
        return _parse_league_csv(body)

    filtered, warnings = filter_mapping(body, LEAGUE_FIELDS, "league")
    league_id = required_str(filtered, "leagueId")
    event_id = required_str(filtered, "eventId")
    rivals = filtered.get("rivals")
    if not isinstance(rivals, list):
        raise ManualImportError("rivals must be a list")
    league: dict[str, object] = {"leagueId": league_id, "eventId": event_id, "rivals": rivals}
    for optional in ["name", "userRank", "gapToLeader"]:
        if optional in filtered:
            league[optional] = filtered[optional]
    return ParsedLeagueImport(league, SNAPSHOT_MANUAL_LEAGUE, warnings, body)


def parse_scores_import(
    payload: dict[str, object],
    market_assets: list[FantasyAsset],
) -> ParsedScoresImport:
    body = as_dict(payload)
    if body.get("format") == "csv":
        return _parse_scores_csv(body, market_assets)

    filtered, warnings = filter_mapping(body, {"eventId", "sourceSnapshotId", "scores"}, "scores")
    event_id = required_str(filtered, "eventId")
    snapshot_id = str(filtered.get("sourceSnapshotId") or SNAPSHOT_MANUAL_SCORES)
    scores_payload, score_warnings = filter_list(
        filtered.get("scores"),
        SCORE_FIELDS,
        "scores.items",
    )
    warnings.extend(score_warnings)
    scores = [_score_row(score, event_id, snapshot_id) for score in scores_payload]
    _validate_score_assets(scores, market_assets)
    return ParsedScoresImport(event_id, scores, snapshot_id, warnings, body)


def _parse_team_csv(
    body: dict[str, object],
    market_assets: list[FantasyAsset],
) -> ParsedTeamImport:
    rows, warnings = read_csv_rows(body, TEAM_ASSET_FIELDS, "team csv")
    market_by_id = {asset.asset_id: asset for asset in market_assets}
    selected = []
    for row in rows:
        asset_id = required_str(row, "assetId")
        market_asset = market_by_id.get(asset_id)
        if market_asset is None:
            raise ManualImportError(f"unknown lineup asset: {asset_id}")
        selected.append(market_asset)
    validation = _validate_lineup_assets(selected, required_float(body, "costCapMillions"))
    team_payload = {
        "teamSnapshotId": required_str(body, "teamSnapshotId"),
        "teamName": required_str(body, "teamName"),
        "eventId": required_str(body, "eventId"),
        "costCapMillions": required_float(body, "costCapMillions"),
        "budgetUsedMillions": validation.budget_used_millions,
        "budgetRemainingMillions": validation.budget_remaining_millions,
        "freeTransfers": required_int(body, "freeTransfers"),
        "capturedAt": required_str(body, "capturedAt"),
        "transferPenaltyPoints": _optional_float(body, "transferPenaltyPoints", 10),
        "sourceSnapshotId": str(body.get("sourceSnapshotId") or SNAPSHOT_MANUAL_TEAM),
        "assets": rows,
        "chips": default_chips(),
    }
    team = _validate_team_model(team_payload)
    return ParsedTeamImport(team, team.source_snapshot_id or SNAPSHOT_MANUAL_TEAM, warnings, body)


def _parse_market_csv(body: dict[str, object]) -> ParsedMarketImport:
    rows, warnings = read_csv_rows(body, ASSET_FIELDS, "market csv")
    event_id = required_str(body, "eventId")
    snapshot_id = str(body.get("sourceSnapshotId") or SNAPSHOT_MANUAL_MARKET)
    assets = [_validate_asset_model(_asset_row(row, snapshot_id)) for row in rows]
    reject_duplicate_ids([asset.asset_id for asset in assets], "market asset")
    return ParsedMarketImport(event_id, assets, snapshot_id, warnings, body)


def _parse_league_csv(body: dict[str, object]) -> ParsedLeagueImport:
    rows, warnings = read_csv_rows(body, {"teamName", "points", "assetIds"}, "league csv")
    league = {
        "leagueId": required_str(body, "leagueId"),
        "eventId": required_str(body, "eventId"),
        "name": body.get("name"),
        "rivals": [
            {
                "teamName": required_str(row, "teamName"),
                "points": required_float(row, "points"),
                "assetIds": split_asset_ids(required_str(row, "assetIds")),
            }
            for row in rows
        ],
    }
    return ParsedLeagueImport(league, SNAPSHOT_MANUAL_LEAGUE, warnings, body)


def _parse_scores_csv(
    body: dict[str, object],
    market_assets: list[FantasyAsset],
) -> ParsedScoresImport:
    rows, warnings = read_csv_rows(body, SCORE_FIELDS, "scores csv")
    event_id = required_str(body, "eventId")
    snapshot_id = str(body.get("sourceSnapshotId") or SNAPSHOT_MANUAL_SCORES)
    scores = [_score_row(row, event_id, snapshot_id) for row in rows]
    _validate_score_assets(scores, market_assets)
    return ParsedScoresImport(event_id, scores, snapshot_id, warnings, body)


def _validate_team_lineup(
    team: FantasyTeamSnapshot,
    market_assets: list[FantasyAsset],
) -> list[str]:
    ids = [asset.asset_id for asset in team.assets]
    reject_duplicate_ids(ids, "lineup asset")
    market_by_id = {asset.asset_id: asset for asset in market_assets}
    missing = sorted(asset_id for asset_id in ids if asset_id not in market_by_id)
    if missing:
        raise ManualImportError(f"unknown lineup assets: {', '.join(missing)}")
    lineup = [market_by_id[asset_id] for asset_id in ids]
    validation = _validate_lineup_assets(lineup, team.cost_cap_millions)
    warnings = []
    if abs(validation.budget_used_millions - team.budget_used_millions) > 0.05:
        warnings.append(
            "declared budgetUsedMillions does not match market prices; imported snapshot kept"
        )
    if abs(validation.budget_remaining_millions - team.budget_remaining_millions) > 0.05:
        warnings.append(
            "declared budgetRemainingMillions does not match market prices; imported snapshot kept"
        )
    return warnings


def _validate_lineup_assets(
    lineup: list[FantasyAsset],
    cost_cap_millions: float,
) -> LineupValidation:
    try:
        return validate_lineup(lineup, cost_cap_millions=cost_cap_millions)
    except InvalidLineup as exc:
        raise ManualImportError(str(exc)) from exc


def _validate_team_model(payload: dict[str, object]) -> FantasyTeamSnapshot:
    try:
        return FantasyTeamSnapshot.model_validate(payload)
    except ValidationError as exc:
        raise ManualImportError(str(exc)) from exc


def _validate_asset_model(payload: dict[str, object]) -> FantasyAsset:
    try:
        return FantasyAsset.model_validate(payload)
    except ValidationError as exc:
        raise ManualImportError(str(exc)) from exc


def _validate_score_model(payload: dict[str, object]) -> FantasyAssetScore:
    try:
        return FantasyAssetScore.model_validate(payload)
    except ValidationError as exc:
        raise ManualImportError(str(exc)) from exc


def _asset_row(row: dict[str, object], snapshot_id: str) -> dict[str, object]:
    parsed = dict(row)
    for field in ["priceMillions", "fantasyPoints", "ownershipPct", "selectedByPct", "riskScore"]:
        if field in parsed:
            parsed[field] = required_float(parsed, field)
    parsed["sourceSnapshotId"] = str(parsed.get("sourceSnapshotId") or snapshot_id)
    return parsed


def _score_row(
    row: dict[str, object],
    event_id: str,
    snapshot_id: str,
) -> FantasyAssetScore:
    parsed = dict(row)
    row_event_id = str(parsed.get("eventId") or event_id)
    if row_event_id != event_id:
        raise ManualImportError(f"score row eventId must match import eventId: {event_id}")
    for field in ["fantasyPoints", "ownershipPct", "selectedByPct"]:
        if field in parsed:
            parsed[field] = required_float(parsed, field)
    parsed["eventId"] = event_id
    parsed["capturedAt"] = parsed.get("capturedAt") or utc_now()
    parsed["sourceSnapshotId"] = str(parsed.get("sourceSnapshotId") or snapshot_id)
    return _validate_score_model(parsed)


def _validate_score_assets(
    scores: list[FantasyAssetScore],
    market_assets: list[FantasyAsset],
) -> None:
    reject_duplicate_ids([score.asset_id for score in scores], "score asset")
    market_ids = {asset.asset_id for asset in market_assets}
    missing = sorted(score.asset_id for score in scores if score.asset_id not in market_ids)
    if missing:
        raise ManualImportError(f"unknown score assets: {', '.join(missing)}")


def _asset_with_snapshot(asset: FantasyAsset, snapshot_id: str) -> FantasyAsset:
    if asset.source_snapshot_id:
        return asset
    return asset.model_copy(update={"source_snapshot_id": snapshot_id})


def _optional_float(payload: dict[str, object], key: str, default: float) -> float:
    return default if payload.get(key) in {None, ""} else required_float(payload, key)
