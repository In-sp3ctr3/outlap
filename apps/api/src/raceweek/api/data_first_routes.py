from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Response, status

from raceweek.connectors.fantasy_normalize import (
    derive_public_history_scores,
    normalize_game_snapshot,
)
from raceweek.connectors.fantasy_readonly import FANTASY_LICENSE_NOTE, FantasyReadOnlyConnector
from raceweek.connectors.import_templates import parse_template
from raceweek.connectors.jolpica import JOLPICA_LICENSE_NOTE, JolpicaConnector
from raceweek.connectors.manual_utils import default_chips
from raceweek.connectors.openf1 import OpenF1Connector, OpenF1Meeting
from raceweek.core.models import (
    ChipState,
    DataFreshness,
    DataInputPath,
    DataMode,
    DataModeRequest,
    DataModeResponse,
    DataResetRequest,
    FantasyAsset,
    FantasyAssetScore,
    FantasyBackfillRequest,
    FantasyBackfillResponse,
    FantasyReadOnlyStatus,
    FantasySyncRequest,
    FantasySyncResponse,
    FantasyTeamSnapshot,
    FreshnessRemediation,
    FreshnessState,
    ImportConfirmRequest,
    ImportConfirmResponse,
    ImportPreviewRequest,
    ImportPreviewResponse,
    OnboardingStatus,
    OnboardingTeamSelectionRequest,
    OnboardingTeamSelectionResponse,
    OptimizerReadiness,
    PublicFormBackfillResponse,
    ReadinessIssue,
    TeamAsset,
    TeamSelectionRequest,
    TeamSelectionResponse,
    TemplateType,
    utc_now,
)
from raceweek.core.rules import InvalidLineup, validate_lineup
from raceweek.settings import settings
from raceweek.storage.demo import REPOSITORY, reload_state, reset_real_data_state, reset_state

router = APIRouter()

FRESHNESS_KEYS: dict[str, tuple[str, int, bool, FreshnessRemediation | None]] = {
    "race.calendar": (
        "Race calendar / schedule",
        7 * 24 * 60 * 60,
        False,
        FreshnessRemediation(label="Sync race context", action="sync_race_context"),
    ),
    "race.current_meeting": (
        "Current or next race meeting",
        24 * 60 * 60,
        False,
        FreshnessRemediation(label="Sync OpenF1/Jolpica", action="sync_race_context"),
    ),
    "race.sessions": (
        "Race sessions",
        6 * 60 * 60,
        False,
        FreshnessRemediation(label="Sync sessions", action="sync_race_context"),
    ),
    "race.weather": (
        "Weather / track conditions",
        30 * 60,
        False,
        FreshnessRemediation(label="Sync weather", action="sync_race_context"),
    ),
    "race.race_control": (
        "Race control",
        5 * 60,
        False,
        FreshnessRemediation(label="Sync race control", action="sync_race_context"),
    ),
    "fantasy.market": (
        "Fantasy market prices",
        24 * 60 * 60,
        True,
        FreshnessRemediation(
            label="Sync Fantasy catalog or provide market data",
            action="sync_fantasy_game",
            template_type="market_prices",
        ),
    ),
    "fantasy.user_team": (
        "User fantasy team",
        24 * 60 * 60,
        True,
        FreshnessRemediation(
            label="Select Team 1-3 from loaded market",
            action="open_team_selector",
            template_type="team_state",
        ),
    ),
    "fantasy.scores": (
        "Fantasy scores",
        24 * 60 * 60,
        False,
        FreshnessRemediation(
            label="Backfill from public results or sync Fantasy scores",
            action="backfill_scores",
            template_type="fantasy_scores",
        ),
    ),
    "fantasy.league": (
        "League table",
        24 * 60 * 60,
        False,
        FreshnessRemediation(
            label="Import league table",
            action="open_import_wizard",
            template_type="league_table",
        ),
    ),
    "ai.provider": (
        "AI provider status",
        24 * 60 * 60,
        False,
        FreshnessRemediation(label="Configure provider", action="open_settings"),
    ),
}

FANTASY_DOCUMENTED_ENDPOINTS = [
    "{game_version}/players",
    "{game_version}/teams",
    "{game_version}/live_stats?game_period_id={game_period_id}",
    "{game_version}/leaderboards/leagues?league_id={league_id}",
    "{game_version}/picked_teams/for_slot?game_period_id={game_period_id}&slot={slot}&user_global_id={user_global_id}",
]

TEAM_COLOR_FALLBACKS = [
    "#2563EB",
    "#059669",
    "#DC2626",
    "#7C3AED",
    "#EA580C",
    "#0F766E",
    "#BE123C",
    "#4F46E5",
]


@router.get("/api/v1/onboarding/status")
def onboarding_status() -> OnboardingStatus:
    mode = _data_mode()
    first_run_completed = bool(REPOSITORY.get_json_setting("first_run_completed", False))
    next_route = "/dashboard" if mode == "demo" else "/onboarding" if mode == "real" else "/"
    return OnboardingStatus(
        first_run_completed=first_run_completed,
        setup_complete=first_run_completed,
        mode=mode,
        next_route=next_route,
        needs_real_data=mode != "demo",
    )


@router.post("/api/v1/onboarding/mode")
def onboarding_mode(request: DataModeRequest) -> DataModeResponse:
    if request.mode == "demo":
        reset_state()
        REPOSITORY.set_json_setting("data_mode", "demo")
        REPOSITORY.set_json_setting("first_run_completed", True)
        REPOSITORY.set_json_setting("allow_demo_fallback", True)
        reload_state()
        return DataModeResponse(mode="demo", allow_demo_fallback=True)

    reset_real_data_state()
    REPOSITORY.set_json_setting("data_mode", "real")
    REPOSITORY.set_json_setting("first_run_completed", True)
    REPOSITORY.set_json_setting("allow_demo_fallback", False)
    reload_state()
    return DataModeResponse(mode="real", allow_demo_fallback=False)


@router.post("/api/v1/onboarding/complete")
def onboarding_complete() -> DataModeResponse:
    REPOSITORY.set_json_setting("data_mode", "real")
    REPOSITORY.set_json_setting("first_run_completed", True)
    REPOSITORY.set_json_setting("allow_demo_fallback", False)
    return DataModeResponse()


@router.get("/api/v1/data-mode")
def data_mode() -> DataModeResponse:
    mode = _data_mode()
    allow_demo_fallback = bool(
        REPOSITORY.get_json_setting("allow_demo_fallback", mode == "demo")
    )
    return DataModeResponse(
        mode=mode,
        allow_demo_fallback=allow_demo_fallback,
    )


@router.put("/api/v1/data-mode")
def update_data_mode() -> DataModeResponse:
    REPOSITORY.set_json_setting("data_mode", "real")
    REPOSITORY.set_json_setting("allow_demo_fallback", False)
    return DataModeResponse()


@router.get("/api/v1/readiness/optimizer")
def optimizer_readiness() -> OptimizerReadiness:
    blocking: list[ReadinessIssue] = []
    warnings: list[ReadinessIssue] = []
    market = REPOSITORY.real_assets()
    teams = REPOSITORY.real_teams()

    if not market:
        blocking.append(
            ReadinessIssue(
                key="fantasy.market",
                label="Fantasy market prices",
                message="Current fantasy prices are missing.",
                recommended_action="Import market prices or run Fantasy token sync.",
            )
        )
    if not teams:
        blocking.append(
            ReadinessIssue(
                key="fantasy.user_team",
                label="Current fantasy team",
                message="Current fantasy team state is missing.",
                recommended_action=(
                    "Select Teams 1-3 from the loaded market or import team templates."
                ),
            )
        )

    market_by_id = {asset.asset_id: asset for asset in market}
    for team in teams[:1]:
        missing_prices = sorted(
            asset.asset_id for asset in team.assets if asset.asset_id not in market_by_id
        )
        if missing_prices:
            blocking.append(
                ReadinessIssue(
                    key="fantasy.team_prices",
                    label="Team asset prices",
                    message=f"Prices are missing for {len(missing_prices)} selected asset(s).",
                    recommended_action=(
                        "Refresh or import market prices for every selected team asset."
                    ),
                )
            )
        try:
            lineup_assets = [
                market_by_id[asset.asset_id]
                for asset in team.assets
                if asset.asset_id in market_by_id
            ]
            validate_lineup(
                lineup_assets,
                cost_cap_millions=team.cost_cap_millions,
            )
        except (InvalidLineup, KeyError) as exc:
            blocking.append(
                ReadinessIssue(
                    key="fantasy.team_validity",
                    label="Team validity",
                    message=str(exc),
                    recommended_action=(
                        "Fix roster composition or budget before running the optimizer."
                    ),
                )
            )

    race_current = REPOSITORY.race_domain_count("race.current_meeting")
    if not race_current:
        warnings.append(
            ReadinessIssue(
                key="race.current_meeting",
                label="Race context",
                message=(
                    "Current or next race context is missing; optimizer can run "
                    "with reduced context."
                ),
                recommended_action="Sync OpenF1/Jolpica race context.",
            )
        )

    return OptimizerReadiness(
        ready=not blocking,
        blocking_reasons=blocking,
        warnings=warnings,
        can_run_with_warnings=not blocking,
    )


@router.post("/api/v1/data/reset")
def reset_data(request: DataResetRequest) -> dict[str, str]:
    if request.scope not in {"all", "manual_imports", "race_context"}:
        raise HTTPException(status_code=400, detail="Unsupported reset scope")
    reset_real_data_state()
    return {"status": "ok", "mode": "real"}


@router.get("/api/v1/imports/templates")
def import_templates() -> dict[str, object]:
    return {
        "items": [
            {"templateType": template, "filename": f"{template}.csv"}
            for template in [
                "team_state",
                "team_slots",
                "market_prices",
                "fantasy_scores",
                "league_table",
                "chips_state",
                "season_totals",
                "transfer_history_optional",
                "rival_team_slots",
            ]
        ]
    }


@router.get("/api/v1/imports/templates/{template_type}.csv")
def import_template_csv(template_type: TemplateType) -> Response:
    template = _template_text(template_type)
    return Response(
        content=template,
        media_type="text/csv",
        headers={"content-disposition": f"attachment; filename={template_type}.csv"},
    )


@router.post("/api/v1/imports/preview")
def imports_preview(request: ImportPreviewRequest) -> ImportPreviewResponse:
    return parse_template(request).preview


@router.post("/api/v1/imports/confirm", status_code=status.HTTP_201_CREATED)
def imports_confirm(request: ImportConfirmRequest) -> ImportConfirmResponse:
    parsed = parse_template(
        ImportPreviewRequest(
            template_type=request.template_type,
            content_type=request.content_type,
            raw_text=request.raw_text,
            filename=request.filename,
        )
    )
    preview = parsed.preview
    if request.content_hash and request.content_hash != preview.content_hash:
        raise HTTPException(status_code=409, detail="Import content changed after preview")
    if not preview.importable:
        raise HTTPException(
            status_code=422,
            detail=[message.model_dump(by_alias=True) for message in preview.messages],
        )

    source_snapshot_id = _snapshot_id(request.template_type, preview.content_hash)
    _record_import_source_snapshot(source_snapshot_id, request, preview)
    item_count = _persist_import(request.template_type, preview, source_snapshot_id)
    job_id = f"import_{request.template_type}_{preview.content_hash[:12]}"
    REPOSITORY.save_import_job(
        job_id=job_id,
        template_type=request.template_type,
        content_hash=preview.content_hash,
        status="imported",
        row_count=item_count,
        summary=f"Imported {item_count} {request.template_type} rows.",
        payload=preview.model_dump(by_alias=True, mode="json"),
    )
    reload_state()
    return ImportConfirmResponse(
        status="imported",
        item_count=item_count,
        job_id=job_id,
        source_snapshot_id=source_snapshot_id,
        message=f"Imported {item_count} {request.template_type} rows.",
        warnings=[message for message in preview.messages if message.severity != "error"],
    )


@router.get("/api/v1/fantasy/sync-requirements")
def fantasy_sync_requirements() -> dict[str, object]:
    return {
        "source": "fantasy_readonly",
        "baseUrlConfigured": bool(settings.fantasy_api_base_url),
        "gameVersionConfigured": bool(settings.fantasy_game_version),
        "sessionTokenConfigured": bool(settings.fantasy_session_token),
        "requiresSessionTokenForPickedTeams": True,
        "requiredEnv": [
            "FANTASY_API_BASE_URL or RACEWEEK_FANTASY_API_BASE_URL",
            "FANTASY_GAME_VERSION or RACEWEEK_FANTASY_GAME_VERSION",
            "FANTASY_SESSION_TOKEN or RACEWEEK_FANTASY_SESSION_TOKEN for current user teams",
        ],
        "message": (
            "Public race context is keyless. Official Fantasy user teams require a "
            "local read-only bearer/session token plus game period and user id."
        ),
    }


@router.get("/api/v1/fantasy/read-only/status")
def fantasy_readonly_status() -> FantasyReadOnlyStatus:
    token_configured = bool(settings.fantasy_session_token)
    return FantasyReadOnlyStatus(
        source="fantasy_readonly",
        status="unknown" if token_configured else "disabled",
        message=(
            "Read-only fantasy connector is locally configured for sync."
            if token_configured
            else (
                "Read-only fantasy sync needs a user-provided local bearer/session "
                "token. Use structured JSON import for market data when no token is "
                "configured; CSV remains available as a fallback."
            )
        ),
        base_url_configured=bool(settings.fantasy_api_base_url),
        game_version_configured=bool(settings.fantasy_game_version),
        session_token_configured=token_configured,
        required_env_vars=[
            "FANTASY_API_BASE_URL",
            "FANTASY_GAME_VERSION",
            "FANTASY_SESSION_TOKEN",
            "RACEWEEK_FANTASY_SESSION_TOKEN",
        ],
        documented_endpoints=FANTASY_DOCUMENTED_ENDPOINTS,
        structured_json_import=DataInputPath(
            label="Structured JSON market/team import",
            endpoint="/api/v1/fantasy/import/market",
            method="POST",
            content_type="application/json",
            primary=True,
        ),
        csv_fallback=DataInputPath(
            label="CSV template import fallback",
            endpoint="/api/v1/imports/confirm",
            method="POST",
            content_type="text/csv",
        ),
        can_mutate_fantasy_account=False,
    )


@router.post("/api/v1/sync/fantasy-game")
async def sync_fantasy_game(request: FantasySyncRequest) -> FantasySyncResponse:
    if not settings.fantasy_game_version:
        raise HTTPException(
            status_code=409,
            detail="Configure FANTASY_GAME_VERSION before syncing read-only Fantasy data.",
        )
    connector = FantasyReadOnlyConnector(
        base_url=settings.fantasy_api_base_url,
        game_version=settings.fantasy_game_version,
        session_token=settings.fantasy_session_token,
    )
    result = await connector.fetch_game_snapshot(
        game_period_id=request.game_period_id,
        league_id=request.league_id,
        slot=request.slot,
        user_global_id=request.user_global_id,
    )
    REPOSITORY.save_connector_result(
        result,
        request_url_template=(
            "https://fantasy-api.formula1.com/partner_games/f1/{game_version}/{path}"
        ),
        license_note=FANTASY_LICENSE_NOTE,
        normalization_version="fantasy-readonly-normalizer-v1",
    )
    event_id = _event_id_from_game_period(request)
    normalized = normalize_game_snapshot(
        result.data,
        event_id=event_id,
        source_snapshot_id=result.raw_snapshot_id,
        slot=request.slot,
    )
    if normalized.assets:
        REPOSITORY.save_assets(event_id, normalized.assets)
    if normalized.scores:
        REPOSITORY.save_scores(event_id, normalized.scores)
    for team in normalized.teams:
        REPOSITORY.save_selected_team(team)
    reload_state()
    return FantasySyncResponse(
        status="ok" if result.status.status == "ok" else "degraded",
        asset_count=len(normalized.assets),
        score_count=len(normalized.scores),
        team_count=len(normalized.teams),
        source_snapshot_id=result.raw_snapshot_id,
        message=(
            "Fantasy catalog synced."
            if normalized.assets
            else (
                "Fantasy sync did not return catalog rows; check token/base URL "
                "or provide market data."
            )
        ),
    )


@router.post("/api/v1/fantasy/public-form/backfill")
async def backfill_public_form_features(
    request: FantasyBackfillRequest,
) -> PublicFormBackfillResponse:
    return await _backfill_public_form_features(request)


@router.post("/api/v1/fantasy/scores/backfill")
async def backfill_fantasy_scores(request: FantasyBackfillRequest) -> FantasyBackfillResponse:
    result = await _backfill_public_form_features(request)
    return FantasyBackfillResponse(
        status=result.status,
        score_count=0,
        source_snapshot_id=result.source_snapshot_id,
        message=(
            "Deprecated endpoint: public race-derived values are saved as "
            "public form features, not official fantasy scores. "
            f"{result.feature_count} feature(s) were saved."
        ),
    )


async def _backfill_public_form_features(
    request: FantasyBackfillRequest,
) -> PublicFormBackfillResponse:
    assets = REPOSITORY.real_assets()
    if not assets:
        raise HTTPException(
            status_code=409,
            detail="Load Fantasy market prices before deriving historical form scores.",
        )
    jolpica = JolpicaConnector()
    result = await jolpica.fetch_season_context(request.season)
    REPOSITORY.save_connector_result(
        result,
        request_url_template="https://api.jolpi.ca/ergast/f1/{path}.json",
        license_note=JOLPICA_LICENSE_NOTE,
        normalization_version="jolpica-historical-form-v1",
    )
    event_id = request.event_id or _event_id_from_round(request.season, request.through_round)
    updated_assets, scores = derive_public_history_scores(
        result.data,
        assets,
        event_id=event_id,
        source_snapshot_id=result.raw_snapshot_id,
        through_round=request.through_round,
    )
    REPOSITORY.save_assets(event_id, updated_assets)
    REPOSITORY.save_public_form_features(
        event_id,
        scores,
        source_snapshot_id=result.raw_snapshot_id,
    )
    reload_state()
    return PublicFormBackfillResponse(
        status="ok" if result.status.status == "ok" else "degraded",
        feature_count=len(scores),
        source_snapshot_id=result.raw_snapshot_id,
        message=(
            "Historical form backfill saved from public race results. "
            "These are deterministic racing-form inputs, not official Fantasy account totals."
        ),
    )


@router.post("/api/v1/onboarding/team-selection", status_code=status.HTTP_201_CREATED)
def save_team_selection(request: TeamSelectionRequest) -> TeamSelectionResponse:
    team = _build_selected_team(request, _real_market_by_id())
    _record_team_selection_snapshot(request, team.source_snapshot_id or "")
    REPOSITORY.save_selected_team(team)
    reload_state()
    return TeamSelectionResponse(
        status="saved",
        team=team,
        message=f"Saved Team {request.slot} from {len(request.asset_ids)} loaded market assets.",
    )


@router.post("/api/v1/onboarding/teams/select", status_code=status.HTTP_201_CREATED)
def save_onboarding_teams(
    request: OnboardingTeamSelectionRequest,
) -> OnboardingTeamSelectionResponse:
    slots = [team.slot for team in request.teams]
    if len(set(slots)) != len(slots):
        raise HTTPException(status_code=422, detail="Team slots must be unique.")

    market = _real_market_by_id()
    team_requests = [
        TeamSelectionRequest(
            team_name=selection.team_name,
            event_id=request.event_id,
            asset_ids=selection.asset_ids,
            slot=selection.slot,
            cost_cap_millions=selection.cost_cap_millions,
            free_transfers=selection.free_transfers,
            transfer_penalty_points=selection.transfer_penalty_points,
        )
        for selection in request.teams
    ]
    teams = [_build_selected_team(team_request, market) for team_request in team_requests]
    for team_request, team in zip(team_requests, teams, strict=True):
        _record_team_selection_snapshot(team_request, team.source_snapshot_id or "")

    REPOSITORY.save_current_teams(teams)
    reload_state()
    return OnboardingTeamSelectionResponse(
        items=teams,
        freshness=_freshness(
            "fantasy.user_team",
            len(teams),
            _latest_fantasy_team_time(),
            source_key=_fantasy_source_key("team"),
            source_mode=_fantasy_source_mode("team"),
        ),
    )


@router.post("/api/v1/sync/race-context")
async def sync_race_context(payload: dict[str, object] | None = None) -> dict[str, object]:
    body = payload or {}
    season = _body_int(body, "season", datetime.now(UTC).year)
    meeting_key = body.get("meetingKey")
    openf1 = OpenF1Connector()
    jolpica = JolpicaConnector()
    if not meeting_key:
        meetings_result = await openf1.fetch_meetings(season)
        if meetings_result.status.status != "ok" or not meetings_result.data:
            raise HTTPException(status_code=502, detail=meetings_result.status.message)
        meeting_key = str(_current_or_next_meeting_key(meetings_result.data))
    openf1_result = await openf1.fetch_session_context(str(meeting_key))
    jolpica_result = await jolpica.fetch_season_context(season)
    row_count = REPOSITORY.save_race_context(openf1_result, jolpica_result)
    current_event_id = _event_id_for_synced_meeting(openf1_result, jolpica_result, season)
    if current_event_id:
        REPOSITORY.set_json_setting("current_event_id", current_event_id)
    REPOSITORY.set_json_setting("current_meeting_key", str(meeting_key))
    response_status = (
        "ok"
        if openf1_result.status.status == "ok" and jolpica_result.status.status == "ok"
        else "degraded"
    )
    return {
        "status": response_status,
        "rowCount": row_count,
        "sourceSnapshotIds": [openf1_result.raw_snapshot_id, jolpica_result.raw_snapshot_id],
        "currentEventId": current_event_id,
        "statuses": [
            openf1_result.status.model_dump(by_alias=True, mode="json"),
            jolpica_result.status.model_dump(by_alias=True, mode="json"),
        ],
        "freshness": _freshness(
            "race.current_meeting",
            REPOSITORY.race_domain_count("race.current_meeting"),
            _latest_race_time("race.current_meeting"),
        ),
    }


@router.get("/api/v1/race-context/current")
def race_context_current() -> dict[str, object]:
    meetings = REPOSITORY.race_meetings()
    current_key = REPOSITORY.get_json_setting("current_meeting_key")
    current = _current_or_next_race_meeting(meetings, current_key)
    return {
        "item": current,
        "freshness": _freshness(
            "race.current_meeting",
            REPOSITORY.race_domain_count("race.current_meeting"),
            _latest_race_time("race.current_meeting"),
        ),
    }


@router.get("/api/v1/race-context/meetings")
def race_context_meetings() -> dict[str, object]:
    meetings = REPOSITORY.race_meetings()
    return {
        "items": meetings,
        "freshness": _freshness(
            "race.calendar",
            REPOSITORY.race_domain_count("race.calendar"),
            _latest_race_time("race.calendar"),
        ),
    }


@router.get("/api/v1/race-context/meetings/{meeting_key}/sessions")
def race_context_sessions(meeting_key: str) -> dict[str, object]:
    sessions = REPOSITORY.race_sessions(meeting_key)
    return {
        "items": sessions,
        "freshness": _freshness(
            "race.sessions",
            len(sessions),
            _latest_race_time("race.sessions"),
        ),
    }


@router.get("/api/v1/fantasy/market")
def fantasy_market() -> dict[str, object]:
    items = REPOSITORY.real_assets()
    return {
        "items": [_catalog_asset(asset) for asset in items],
        "freshness": _freshness(
            "fantasy.market",
            len(items),
            _latest_fantasy_market_time(),
            source_key=_fantasy_source_key("market"),
            source_mode=_fantasy_source_mode("market"),
        ),
    }


@router.get("/api/v1/fantasy/team/current")
def fantasy_team_current() -> dict[str, object]:
    items = sorted(REPOSITORY.real_teams(), key=lambda team: team.slot or 99)
    pending = REPOSITORY.get_json_setting("pending_team_state")
    status_override: FreshnessState | None = (
        "partial" if not items and isinstance(pending, dict) else None
    )
    return {
        "items": items,
        "freshness": _freshness(
            "fantasy.user_team",
            len(items),
            _latest_fantasy_team_time(),
            status_override=status_override,
            source_key=_fantasy_source_key("team"),
            source_mode=_fantasy_source_mode("team"),
        ),
    }


@router.get("/api/v1/fantasy/scores")
def fantasy_scores(eventId: str | None = None) -> dict[str, object]:
    items = REPOSITORY.real_scores(eventId)
    return {
        "items": items,
        "freshness": _freshness(
            "fantasy.scores",
            len(items),
            _latest_fantasy_scores_time(),
            source_key=_fantasy_source_key("scores"),
            source_mode=_fantasy_source_mode("scores"),
        ),
    }


@router.get("/api/v1/fantasy/league")
def fantasy_league() -> dict[str, object]:
    league = REPOSITORY.real_league()
    items = [] if league is None else [league]
    return {
        "items": items,
        "freshness": _freshness("fantasy.league", len(items), _latest_manual_snapshot("league")),
    }


@router.get("/api/v1/data-freshness")
def data_freshness() -> dict[str, object]:
    items = _freshness_items()
    return {"items": items, "overallStatus": _overall_status(items)}


def _freshness_items() -> list[DataFreshness]:
    market = REPOSITORY.real_assets()
    teams = REPOSITORY.real_teams()
    scores = REPOSITORY.real_scores()
    league = REPOSITORY.real_league()
    pending = REPOSITORY.get_json_setting("pending_team_state")
    items = [
        _freshness(
            "race.calendar",
            REPOSITORY.race_domain_count("race.calendar"),
            _latest_race_time("race.calendar"),
        ),
        _freshness(
            "race.current_meeting",
            REPOSITORY.race_domain_count("race.current_meeting"),
            _latest_race_time("race.current_meeting"),
        ),
        _freshness(
            "race.sessions",
            REPOSITORY.race_domain_count("race.sessions"),
            _latest_race_time("race.sessions"),
        ),
        _freshness(
            "race.weather",
            REPOSITORY.race_domain_count("race.weather"),
            _latest_race_time("race.weather"),
        ),
        _freshness(
            "race.race_control",
            REPOSITORY.race_domain_count("race.race_control"),
            _latest_race_time("race.race_control"),
        ),
        _freshness(
            "fantasy.market",
            len(market),
            _latest_fantasy_market_time(),
            source_key=_fantasy_source_key("market"),
            source_mode=_fantasy_source_mode("market"),
        ),
        _freshness(
            "fantasy.user_team",
            len(teams),
            _latest_fantasy_team_time(),
            status_override="partial" if not teams and isinstance(pending, dict) else None,
            source_key=_fantasy_source_key("team"),
            source_mode=_fantasy_source_mode("team"),
        ),
        _freshness(
            "fantasy.scores",
            len(scores),
            _latest_fantasy_scores_time(),
            source_key=_fantasy_source_key("scores"),
            source_mode=_fantasy_source_mode("scores"),
        ),
        _freshness("fantasy.league", 0 if league is None else 1, _latest_manual_snapshot("league")),
        _provider_freshness(),
    ]
    return items


@router.get("/api/v1/data-freshness/{key}")
def data_freshness_item(key: str) -> DataFreshness:
    for item in _freshness_items():
        if item.key == key:
            return item
    raise HTTPException(status_code=404, detail="Freshness key not found")


def _persist_import(
    template_type: TemplateType,
    preview: ImportPreviewResponse,
    source_snapshot_id: str,
) -> int:
    if template_type == "market_prices":
        assets = [
            FantasyAsset.model_validate({**row, "sourceSnapshotId": source_snapshot_id})
            for row in preview.rows
        ]
        REPOSITORY.save_assets(_event_id_from_rows(preview.rows), assets)
        return len(assets)
    if template_type == "team_state":
        state = preview.rows[0]
        REPOSITORY.set_json_setting(
            "pending_team_state",
            {**state, "sourceSnapshotId": source_snapshot_id},
        )
        return len(preview.rows)
    if template_type == "team_slots":
        _save_team_slots(preview, source_snapshot_id)
        return len(preview.rows)
    if template_type == "fantasy_scores":
        scores = [
            FantasyAssetScore.model_validate(
                {
                    "assetId": row["assetId"],
                    "eventId": row["eventId"],
                    "fantasyPoints": row["fantasyPoints"],
                    "capturedAt": utc_now(),
                    "sourceSnapshotId": source_snapshot_id,
                }
            )
            for row in preview.rows
        ]
        REPOSITORY.save_scores(_event_id_from_rows(preview.rows), scores)
        return len(scores)
    if template_type in {
        "chips_state",
        "season_totals",
        "transfer_history_optional",
    }:
        REPOSITORY.set_json_setting(
            f"manual_{template_type}",
            {"rows": preview.rows, "sourceSnapshotId": source_snapshot_id},
        )
        return len(preview.rows)
    if template_type == "rival_team_slots":
        REPOSITORY.save_real_league(
            _rival_slots_league_payload(preview, source_snapshot_id)
        )
        return len(preview.rows)

    league: dict[str, object] = {
        "leagueId": preview.rows[0].get("leagueId") or f"league_manual_{source_snapshot_id[-12:]}",
        "eventId": _event_id_from_rows(preview.rows),
        "rivals": [
            {
                "rank": row["leagueRank"],
                "teamName": row["teamName"],
                "points": row["totalPoints"],
                "assetIds": row["assetIds"],
            }
            for row in preview.rows
        ],
        "sourceSnapshotId": source_snapshot_id,
    }
    REPOSITORY.save_real_league(league)
    return len(preview.rows)


def _save_team_slots(preview: ImportPreviewResponse, source_snapshot_id: str) -> None:
    state = REPOSITORY.get_json_setting("pending_team_state")
    if not isinstance(state, dict):
        raise HTTPException(
            status_code=422,
            detail="Import team_state before team_slots so budget and transfers are known.",
        )
    assets = [
        TeamAsset.model_validate(
            {
                "assetId": row["assetId"],
                "assetType": row["assetType"],
                "boostMultiplier": row.get("boostMultiplier") or 1,
            }
        )
        for row in preview.rows
    ]
    cost_cap = float(state["costCapMillions"])
    budget_remaining = float(state["budgetRemainingMillions"])
    event_id = str(state["eventId"])
    slot = int(state.get("slot") or preview.rows[0].get("slotNumber") or 1)
    team = FantasyTeamSnapshot(
        team_snapshot_id=f"team_manual_{source_snapshot_id[-12:]}",
        team_name=str(state["teamName"]),
        event_id=event_id,
        cost_cap_millions=cost_cap,
        budget_used_millions=float(state.get("budgetUsedMillions") or cost_cap - budget_remaining),
        budget_remaining_millions=budget_remaining,
        free_transfers=int(state["freeTransfers"]),
        transfer_penalty_points=float(state.get("transferPenaltyPoints") or 10),
        captured_at=utc_now(),
        source_snapshot_id=source_snapshot_id,
        slot=slot,
        assets=assets,
        chips=_chips_for_slot(slot, event_id),
    )
    REPOSITORY.save_team(team)


def _chips_for_slot(slot: int, event_id: str) -> list[ChipState]:
    setting = REPOSITORY.get_json_setting("manual_chips_state")
    rows = setting.get("rows", []) if isinstance(setting, dict) else []
    chips: dict[str, dict[str, object]] = {
        chip["chipName"]: {
            "chipName": chip["chipName"],
            "status": chip["status"],
        }
        for chip in default_chips()
    }
    for row in rows:
        if not isinstance(row, dict):
            continue
        row_slot = int(row.get("slot") or slot)
        row_event_id = row.get("eventId") or event_id
        if row_slot != slot or row_event_id != event_id:
            continue
        chip_name = str(row.get("chipName") or "").lower()
        if chip_name:
            chips[chip_name] = {
                "chipName": chip_name,
                "status": row.get("status") or "unknown",
                "usedEventId": row.get("usedEventId"),
            }
    return [ChipState.model_validate(chip) for chip in chips.values()]


def _rival_slots_league_payload(
    preview: ImportPreviewResponse,
    source_snapshot_id: str,
) -> dict[str, object]:
    rows = preview.rows
    league_id = next((row.get("leagueId") for row in rows if row.get("leagueId")), None)
    rivals_by_name: dict[str, dict[str, object]] = {}
    for row in rows:
        team_name = str(row["teamName"])
        rival = rivals_by_name.setdefault(
            team_name,
            {
                "rank": row.get("leagueRank") or 0,
                "teamName": team_name,
                "points": 0,
                "assetIds": [],
            },
        )
        asset_ids = rival["assetIds"]
        if isinstance(asset_ids, list):
            asset_ids.append(row["assetId"])
    return {
        "leagueId": league_id or f"league_manual_{source_snapshot_id[-12:]}",
        "eventId": _event_id_from_rows(rows),
        "rivals": list(rivals_by_name.values()),
        "sourceSnapshotId": source_snapshot_id,
    }


def _catalog_asset(asset: FantasyAsset) -> dict[str, object]:
    payload = asset.model_dump(by_alias=True, mode="json")
    abbreviation = _asset_abbreviation(asset)
    payload["shortName"] = abbreviation
    payload["abbreviation"] = asset.abbreviation or abbreviation
    payload["teamColor"] = _asset_team_color(asset)
    return payload


def _asset_abbreviation(asset: FantasyAsset) -> str:
    explicit = asset.short_name or asset.abbreviation
    if explicit:
        return explicit.strip().upper()
    words = "".join(
        character if character.isalnum() else " "
        for character in asset.display_name
    ).split()
    if asset.asset_type == "driver" and words:
        return (words[-1][:3] or "UNK").upper()
    if len(words) >= 2:
        return "".join(word[0] for word in words[:3]).upper()
    return ((words[0] if words else asset.display_name)[:3] or "UNK").upper()


def _asset_team_color(asset: FantasyAsset) -> str:
    if asset.team_color_hex:
        return asset.team_color_hex.upper()
    key = asset.constructor_name or asset.display_name or asset.asset_id
    digest = hashlib.sha256(key.encode()).hexdigest()
    index = int(digest[:8], 16) % len(TEAM_COLOR_FALLBACKS)
    return TEAM_COLOR_FALLBACKS[index]


def _real_market_by_id() -> dict[str, FantasyAsset]:
    assets = REPOSITORY.real_assets()
    if not assets:
        raise HTTPException(
            status_code=409,
            detail="Load fantasy market/catalog data before setup team selection.",
        )
    return {asset.asset_id: asset for asset in assets}


def _build_selected_team(
    request: TeamSelectionRequest,
    market: dict[str, FantasyAsset],
) -> FantasyTeamSnapshot:
    missing = sorted(asset_id for asset_id in request.asset_ids if asset_id not in market)
    if missing:
        raise HTTPException(status_code=422, detail=f"Unknown market assets: {', '.join(missing)}")
    if len(set(request.asset_ids)) != len(request.asset_ids):
        raise HTTPException(status_code=422, detail="Team selection cannot contain duplicates.")

    lineup = [market[asset_id] for asset_id in request.asset_ids]
    try:
        validation = validate_lineup(lineup, cost_cap_millions=request.cost_cap_millions)
    except InvalidLineup as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    content_hash = _hash_json(request.model_dump(by_alias=True, mode="json"))
    source_snapshot_id = f"snapshot_user_selection_slot_{request.slot}_{content_hash[:12]}"
    return FantasyTeamSnapshot(
        team_snapshot_id=f"team_slot_{request.slot}_{content_hash[:12]}",
        team_name=request.team_name,
        event_id=request.event_id,
        cost_cap_millions=request.cost_cap_millions,
        budget_used_millions=validation.budget_used_millions,
        budget_remaining_millions=validation.budget_remaining_millions,
        free_transfers=request.free_transfers,
        transfer_penalty_points=request.transfer_penalty_points,
        captured_at=utc_now(),
        source_snapshot_id=source_snapshot_id,
        slot=request.slot,
        assets=[
            TeamAsset(asset_id=asset.asset_id, asset_type=asset.asset_type)
            for asset in lineup
        ],
        chips=[ChipState.model_validate(chip) for chip in default_chips()],
    )


def _record_team_selection_snapshot(
    request: TeamSelectionRequest,
    source_snapshot_id: str,
) -> None:
    REPOSITORY.save_source_snapshot(
        source_snapshot_id,
        {
            "teamName": request.team_name,
            "eventId": request.event_id,
            "slot": request.slot,
            "assetIds": request.asset_ids,
        },
        source_name="user_team_selection",
        connector_version="team-selection-v1",
        request_url_template="local://onboarding/team-selection",
    )


def _freshness(
    key: str,
    record_count: int,
    last_success_at: datetime | None,
    *,
    status_override: FreshnessState | None = None,
    source_key: str | None = None,
    source_mode: Literal["real", "manual", "advanced_token", "demo", "none"] | None = None,
) -> DataFreshness:
    label, stale_after, blocking, remediation = FRESHNESS_KEYS[key]
    status_value = status_override or ("real_current" if record_count > 0 else "missing")
    age = _age_seconds(last_success_at)
    if status_value == "real_current" and age is not None and age > stale_after:
        status_value = "real_stale"
    message = _freshness_message(label, status_value, record_count)
    return DataFreshness(
        key=key,
        label=label,
        status=status_value,
        source_key=source_key if record_count else None,
        source_mode=source_mode or ("manual" if record_count else "none"),
        last_success_at=last_success_at,
        last_attempt_at=last_success_at,
        age_seconds=age,
        stale_after_seconds=stale_after,
        record_count=record_count,
        is_blocking=blocking,
        message=message,
        remediation=None if record_count else remediation,
    )


def _provider_freshness() -> DataFreshness:
    configs = REPOSITORY.load_provider_configs()
    configured = sum(
        1
        for config in configs
        if config.key_configured or config.provider_name == "fake"
    )
    message = (
        "A local/fake provider is available."
        if configured
        else "No AI provider configured."
    )
    return DataFreshness(
        key="ai.provider",
        label=FRESHNESS_KEYS["ai.provider"][0],
        status="real_current" if configured else "missing",
        source_key="provider_config",
        source_mode="real",
        stale_after_seconds=FRESHNESS_KEYS["ai.provider"][1],
        record_count=configured,
        is_blocking=False,
        message=message,
        remediation=None if configured else FRESHNESS_KEYS["ai.provider"][3],
    )


def _record_import_source_snapshot(
    snapshot_id: str,
    request: ImportConfirmRequest,
    preview: ImportPreviewResponse,
) -> None:
    REPOSITORY.save_source_snapshot(
        snapshot_id,
        {
            "templateType": request.template_type,
            "contentHash": preview.content_hash,
            "rowCount": preview.row_count,
            "rows": preview.rows,
        },
        request_url_template=f"manual://imports/{request.template_type}",
    )


def _latest_manual_snapshot(domain: str) -> datetime | None:
    value = REPOSITORY.latest_snapshot_time(f"snapshot_manual_{domain}")
    return _coerce_datetime(value)


def _latest_fantasy_market_time() -> datetime | None:
    return _latest_source_time(
        [
            "snapshot_fantasy_readonly",
            "snapshot_manual_market",
        ]
    )


def _latest_fantasy_team_time() -> datetime | None:
    return _latest_source_time(
        [
            "snapshot_user_selection",
            "snapshot_fantasy_readonly",
            "snapshot_manual_team",
        ]
    )


def _latest_fantasy_scores_time() -> datetime | None:
    return _latest_source_time(
        [
            "snapshot_fantasy_readonly",
            "snapshot_jolpica",
            "snapshot_manual_scores",
        ]
    )


def _latest_source_time(prefixes: list[str]) -> datetime | None:
    values = [
        _coerce_datetime(REPOSITORY.latest_snapshot_time(prefix))
        for prefix in prefixes
    ]
    present = [value for value in values if value is not None]
    return max(present) if present else None


def _fantasy_source_key(domain: Literal["market", "team", "scores"]) -> str | None:
    source = _latest_fantasy_source(domain)
    return None if source is None else source[0]


def _fantasy_source_mode(
    domain: Literal["market", "team", "scores"],
) -> Literal["real", "manual", "advanced_token", "demo", "none"] | None:
    source = _latest_fantasy_source(domain)
    return None if source is None else source[1]


def _latest_fantasy_source(
    domain: Literal["market", "team", "scores"],
) -> tuple[str, Literal["real", "manual", "advanced_token", "demo", "none"]] | None:
    candidates: dict[
        str,
        list[tuple[str, str, Literal["real", "manual", "advanced_token", "demo", "none"]]],
    ] = {
        "market": [
            ("snapshot_fantasy_readonly", "fantasy_readonly", "advanced_token"),
            ("snapshot_manual_market", "manual_import", "manual"),
        ],
        "team": [
            ("snapshot_user_selection", "user_team_selection", "real"),
            ("snapshot_fantasy_readonly", "fantasy_readonly", "advanced_token"),
            ("snapshot_manual_team", "manual_import", "manual"),
        ],
        "scores": [
            ("snapshot_fantasy_readonly", "fantasy_readonly", "advanced_token"),
            ("snapshot_jolpica", "jolpica_historical_form", "real"),
            ("snapshot_manual_scores", "manual_import", "manual"),
        ],
    }
    dated = [
        (_coerce_datetime(REPOSITORY.latest_snapshot_time(prefix)), source_key, source_mode)
        for prefix, source_key, source_mode in candidates[domain]
    ]
    present = [item for item in dated if item[0] is not None]
    if not present:
        return None
    _, source_key, source_mode = max(present, key=lambda item: item[0] or datetime.min)
    return source_key, source_mode


def _latest_race_time(domain: str) -> datetime | None:
    return _coerce_datetime(REPOSITORY.latest_race_context_time(domain))


def _coerce_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str) and value.strip():
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    return None


def _age_seconds(value: datetime | None) -> int | None:
    if value is None:
        return None
    return max(0, int((utc_now() - value).total_seconds()))


def _event_id_from_rows(rows: list[dict[str, Any]]) -> str:
    event_id = next((row.get("eventId") for row in rows if row.get("eventId")), None)
    return str(event_id or "event_manual")


def _event_id_from_game_period(request: FantasySyncRequest) -> str:
    if request.game_period_id.startswith("event_"):
        return request.game_period_id
    season = request.season or datetime.now(UTC).year
    digits = "".join(char for char in request.game_period_id if char.isdigit())
    if digits:
        return _event_id_from_round(season, int(digits))
    return f"event_{season}_{request.game_period_id}"


def _event_id_from_round(season: int, round_number: int | None) -> str:
    if round_number:
        return f"event_{season}_{round_number:02d}"
    return f"event_{season}_season_to_date"


def _event_id_for_synced_meeting(
    openf1_result: Any,
    jolpica_result: Any,
    season: int,
) -> str | None:
    meeting_names = {
        _normalized_name(getattr(meeting, "meeting_name", None))
        for meeting in getattr(openf1_result.data, "meetings", [])
        if getattr(meeting, "meeting_name", None)
    }
    for race in getattr(jolpica_result.data, "races", []):
        race_name = _normalized_name(getattr(race, "race_name", None))
        if race_name and race_name in meeting_names:
            return _event_id_from_round(season, int(race.round_number))

    races = list(getattr(jolpica_result.data, "races", []))
    if not races:
        return None
    now = utc_now()
    dated = [race for race in races if getattr(race, "starts_at", None) is not None]
    if not dated:
        return _event_id_from_round(season, int(races[0].round_number))
    upcoming = [
        race
        for race in dated
        if (_coerce_datetime(getattr(race, "starts_at", None)) or now) >= now
    ]
    selected = min(
        upcoming or dated,
        key=lambda race: abs(
            ((_coerce_datetime(getattr(race, "starts_at", None)) or now) - now).total_seconds()
        ),
    )
    return _event_id_from_round(season, int(selected.round_number))


def _normalized_name(value: object) -> str:
    return "".join(char.lower() for char in str(value or "") if char.isalnum())


def _current_or_next_meeting_key(meetings: list[OpenF1Meeting]) -> str | int:
    now = utc_now()
    with_dates = [
        meeting
        for meeting in meetings
        if getattr(meeting, "date_start", None) is not None
    ]
    if not with_dates:
        return meetings[0].meeting_key
    upcoming = [
        meeting
        for meeting in with_dates
        if _coerce_datetime(getattr(meeting, "date_end", None)) is None
        or (_coerce_datetime(getattr(meeting, "date_end", None)) or now) >= now
    ]
    selected = min(
        upcoming or with_dates,
        key=lambda meeting: abs(
            ((_coerce_datetime(getattr(meeting, "date_start", None)) or now) - now).total_seconds()
        ),
    )
    return selected.meeting_key


def _current_or_next_race_meeting(
    meetings: list[dict[str, Any]],
    current_key: object,
    *,
    now: datetime | None = None,
) -> dict[str, Any] | None:
    if not meetings:
        return None
    if isinstance(current_key, str):
        exact = next(
            (meeting for meeting in meetings if meeting.get("meetingKey") == current_key),
            None,
        )
        if exact is not None:
            return exact

    reference_time = now or utc_now()
    dated = [
        (
            _coerce_datetime(meeting.get("startsAt")),
            _coerce_datetime(meeting.get("endsAt")),
            meeting,
        )
        for meeting in meetings
    ]
    active = [
        (start, meeting)
        for start, end, meeting in dated
        if start is not None and end is not None and start <= reference_time <= end
    ]
    if active:
        return min(active, key=lambda item: item[0])[1]

    upcoming = [
        (start, meeting)
        for start, _end, meeting in dated
        if start is not None and start >= reference_time
    ]
    if upcoming:
        return min(upcoming, key=lambda item: item[0])[1]

    past = [
        (start, meeting)
        for start, _end, meeting in dated
        if start is not None and start < reference_time
    ]
    if past:
        return max(past, key=lambda item: item[0])[1]

    return meetings[0]


def _hash_json(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def _snapshot_id(template_type: TemplateType, content_hash: str) -> str:
    domain = {
        "market_prices": "market",
        "team_state": "team_state",
        "team_slots": "team",
        "fantasy_scores": "scores",
        "league_table": "league",
        "chips_state": "chips",
        "season_totals": "season_totals",
        "transfer_history_optional": "transfers",
        "rival_team_slots": "league",
    }[template_type]
    return f"snapshot_manual_{domain}_{content_hash[:12]}"


def _freshness_message(label: str, status_value: str, record_count: int) -> str:
    if status_value == "missing":
        return f"No {label.lower()} has been imported or synced yet."
    if status_value == "partial":
        return f"{label} is partially imported; complete the remaining template."
    if status_value == "real_stale":
        return f"{label} exists but is older than the freshness threshold."
    return f"{label} has {record_count} real imported record(s)."


def _overall_status(items: list[DataFreshness]) -> str:
    if any(item.is_blocking and item.status == "missing" for item in items):
        return "missing"
    if any(item.is_blocking and item.status == "real_stale" for item in items):
        return "real_stale"
    if any(item.status in {"missing", "partial", "real_stale"} for item in items):
        return "partial"
    return "real_current"


def _template_text(template_type: TemplateType) -> str:
    templates = {
        "team_state": (
            "season,event_id,slot,team_name,cost_cap_millions,"
            "budget_used_millions,budget_remaining_millions,free_transfers,"
            "transfer_penalty_points,total_points,source_note\n"
        ),
        "team_slots": (
            "season,event_id,slot,asset_id,asset_type,display_name,"
            "constructor_name,boost_multiplier,source_note\n"
        ),
        "market_prices": (
            "season,event_id,asset_id,asset_type,display_name,constructor_name,"
            "price_millions,ownership_pct,selected_by_pct,source_note\n"
        ),
        "fantasy_scores": (
            "season,event_id,asset_id,asset_type,display_name,"
            "official_fantasy_points,source_note\n"
        ),
        "league_table": (
            "season,event_id,league_id,league_name,rank,entry_name,manager_name,"
            "total_points,round_points,source_note\n"
        ),
        "chips_state": "season,event_id,slot,chip_name,status,used_event_id,source_note\n",
        "season_totals": (
            "season,event_id,slot,team_name,total_points,overall_rank,"
            "league_rank,source_note\n"
        ),
        "transfer_history_optional": (
            "season,event_id,slot,transfer_number,out_asset_id,out_display_name,"
            "in_asset_id,in_display_name,penalty_points,chip_active,source_note\n"
        ),
        "rival_team_slots": (
            "season,event_id,league_id,entry_name,rank,asset_id,asset_type,"
            "display_name,constructor_name,source_note\n"
        ),
    }
    return templates[template_type]


def _body_int(body: dict[str, object], key: str, default: int) -> int:
    value = body.get(key)
    if value is None or value == "":
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    raise HTTPException(status_code=422, detail=f"{key} must be an integer")


def _data_mode() -> DataMode:
    value = REPOSITORY.get_json_setting("data_mode", "unset")
    return value if value in {"unset", "demo", "real"} else "unset"
