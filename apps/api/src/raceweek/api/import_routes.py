from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, HTTPException, status

from raceweek.connectors.manual import (
    parse_league_import,
    parse_market_import,
    parse_scores_import,
    parse_team_import,
)
from raceweek.connectors.manual_types import ManualImportError
from raceweek.core.models import ImportResult
from raceweek.storage.demo import (
    get_state,
    record_source_snapshot,
    replace_assets,
    replace_league,
    replace_scores,
    replace_team,
)

router = APIRouter()


@router.post("/api/v1/fantasy/import/team", status_code=status.HTTP_201_CREATED)
def import_team(payload: dict[str, object]) -> ImportResult:
    imported = _parse_import(lambda: parse_team_import(payload, get_state().assets))
    record_source_snapshot(
        imported.source_snapshot_id,
        imported.raw_payload,
        request_url_template="manual://fantasy/team",
    )
    replace_team(imported.team)
    return ImportResult(
        status="imported",
        item_count=len(imported.team.assets),
        source_snapshot_id=imported.source_snapshot_id,
        message="Team snapshot imported. Manual action remains required for transfers.",
        warnings=imported.warnings,
    )


@router.post("/api/v1/fantasy/import/market", status_code=status.HTTP_201_CREATED)
def import_market(payload: dict[str, object]) -> ImportResult:
    imported = _parse_import(lambda: parse_market_import(payload))
    record_source_snapshot(
        imported.source_snapshot_id,
        imported.raw_payload,
        request_url_template="manual://fantasy/market",
    )
    replace_assets(imported.event_id, imported.assets)
    return ImportResult(
        status="imported",
        item_count=len(imported.assets),
        source_snapshot_id=imported.source_snapshot_id,
        message="Market snapshot imported.",
        warnings=imported.warnings,
    )


@router.post("/api/v1/fantasy/import/scores", status_code=status.HTTP_201_CREATED)
def import_scores(payload: dict[str, object]) -> ImportResult:
    imported = _parse_import(lambda: parse_scores_import(payload, get_state().assets))
    record_source_snapshot(
        imported.source_snapshot_id,
        imported.raw_payload,
        request_url_template="manual://fantasy/scores",
    )
    replace_scores(imported.event_id, imported.scores)
    return ImportResult(
        status="imported",
        item_count=len(imported.scores),
        source_snapshot_id=imported.source_snapshot_id,
        message="Fantasy score snapshot imported.",
        warnings=imported.warnings,
    )


@router.post("/api/v1/leagues/import", status_code=status.HTTP_201_CREATED)
def import_league(payload: dict[str, object]) -> ImportResult:
    imported = _parse_import(lambda: parse_league_import(payload))
    record_source_snapshot(
        imported.source_snapshot_id,
        imported.raw_payload,
        request_url_template="manual://league",
    )
    replace_league(imported.league)
    return ImportResult(
        status="imported",
        item_count=_count_imported_items(imported.league.get("rivals")),
        source_snapshot_id=imported.source_snapshot_id,
        message="League snapshot imported for local analysis.",
        warnings=imported.warnings,
    )


def _parse_import[ParsedImport](parse: Callable[[], ParsedImport]) -> ParsedImport:
    try:
        return parse()
    except ManualImportError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _count_imported_items(value: object) -> int:
    return len(value) if isinstance(value, list) else 0
