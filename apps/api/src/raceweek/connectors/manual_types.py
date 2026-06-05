from __future__ import annotations

from dataclasses import dataclass

from raceweek.core.models import FantasyAsset, FantasyAssetScore, FantasyTeamSnapshot

SNAPSHOT_MANUAL_MARKET = "snapshot_manual_market"
SNAPSHOT_MANUAL_TEAM = "snapshot_manual_team"
SNAPSHOT_MANUAL_LEAGUE = "snapshot_manual_league"
SNAPSHOT_MANUAL_SCORES = "snapshot_manual_scores"

TEAM_FIELDS = {
    "teamSnapshotId",
    "teamName",
    "eventId",
    "costCapMillions",
    "budgetUsedMillions",
    "budgetRemainingMillions",
    "freeTransfers",
    "assets",
    "chips",
    "capturedAt",
    "slot",
    "transferPenaltyPoints",
    "sourceSnapshotId",
}
TEAM_ASSET_FIELDS = {"assetId", "assetType", "boostMultiplier"}
CHIP_FIELDS = {"chipName", "status", "usedEventId"}
MARKET_FIELDS = {"eventId", "sourceSnapshotId", "assets"}
ASSET_FIELDS = {
    "assetId",
    "assetType",
    "displayName",
    "externalId",
    "shortName",
    "constructorName",
    "priceMillions",
    "fantasyPoints",
    "ownershipPct",
    "selectedByPct",
    "pointsPerMillion",
    "riskScore",
    "sourceSnapshotId",
}
LEAGUE_FIELDS = {"leagueId", "eventId", "name", "rivals", "userRank", "gapToLeader"}
SCORE_FIELDS = {
    "assetId",
    "eventId",
    "fantasyPoints",
    "ownershipPct",
    "selectedByPct",
    "capturedAt",
    "sourceSnapshotId",
}


class ManualImportError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedTeamImport:
    team: FantasyTeamSnapshot
    source_snapshot_id: str
    warnings: list[str]
    raw_payload: dict[str, object]


@dataclass(frozen=True)
class ParsedMarketImport:
    event_id: str
    assets: list[FantasyAsset]
    source_snapshot_id: str
    warnings: list[str]
    raw_payload: dict[str, object]


@dataclass(frozen=True)
class ParsedLeagueImport:
    league: dict[str, object]
    source_snapshot_id: str
    warnings: list[str]
    raw_payload: dict[str, object]


@dataclass(frozen=True)
class ParsedScoresImport:
    event_id: str
    scores: list[FantasyAssetScore]
    source_snapshot_id: str
    warnings: list[str]
    raw_payload: dict[str, object]
