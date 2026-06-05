from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from raceweek import __version__
from raceweek.agents import answer_chat
from raceweek.core.models import (
    AgentChatRequest,
    AgentChatResponse,
    AgentConversation,
    FantasyAsset,
    FantasyTeamSnapshot,
    ImportResult,
    LeagueAnalysis,
    LeagueImportRequest,
    OptimizerRequest,
    ProjectionRunResult,
    RaceMeeting,
    RaceSession,
    RaceWeekIntelligence,
    RecommendationRunResult,
    SyncRequest,
    SyncResult,
    utc_now,
)
from raceweek.core.optimizer import optimize_recommendations
from raceweek.core.projections import run_projection
from raceweek.storage.demo import (
    analyze_league,
    get_state,
    provider_configs,
    replace_assets,
    replace_team,
    reset_state,
    simulate_openf1_failure,
)

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/v1/demo/reset")
def demo_reset() -> dict[str, str]:
    reset_state()
    return {"status": "ok"}


@router.get("/api/v1/app/status")
def app_status() -> dict[str, object]:
    state = get_state()
    return {
        "version": __version__,
        "setupComplete": True,
        "databaseReady": True,
        "currentEventId": state.current_event_id,
    }


@router.get("/api/v1/data-sources/status")
def data_source_status() -> dict[str, object]:
    return {"items": list(get_state().data_sources.values())}


@router.get("/api/v1/providers")
def providers() -> dict[str, object]:
    return {"items": provider_configs()}


@router.post("/api/v1/providers/test")
def provider_test(payload: dict[str, object]) -> dict[str, object]:
    provider = str(payload.get("providerName", "fake"))
    if provider == "fake-fail":
        return {"ok": False, "message": "Fake provider failure path verified."}
    return {"ok": True, "message": "Provider configuration is valid for demo mode."}


@router.post("/api/v1/fantasy/import/team", status_code=status.HTTP_201_CREATED)
def import_team(team: FantasyTeamSnapshot) -> ImportResult:
    replace_team(team)
    return ImportResult(
        status="imported",
        item_count=len(team.assets),
        source_snapshot_id=team.source_snapshot_id or "snapshot_manual_team",
        message="Team snapshot imported. Manual action remains required for transfers.",
    )


@router.post("/api/v1/fantasy/import/market", status_code=status.HTTP_201_CREATED)
def import_market(payload: dict[str, object]) -> ImportResult:
    event_id = str(payload["eventId"])
    assets_payload = payload.get("assets")
    if not isinstance(assets_payload, list):
        raise HTTPException(status_code=422, detail="assets must be a list")
    assets = [FantasyAsset.model_validate(asset) for asset in assets_payload]
    replace_assets(event_id, assets)
    return ImportResult(
        status="imported",
        item_count=len(assets),
        source_snapshot_id="snapshot_manual_market",
        message="Market snapshot imported.",
    )


@router.post("/api/v1/fantasy/sync", status_code=status.HTTP_202_ACCEPTED)
def sync_fantasy(request: SyncRequest | None = None) -> SyncResult:
    if request and request.simulate_failure:
        simulate_openf1_failure()
        return SyncResult(
            status="degraded",
            message="OpenF1 demo connector failed; local snapshot remains usable.",
            source_snapshot_ids=["snapshot_demo_market_01"],
        )
    return SyncResult(
        status="ok",
        message="Demo sources are fresh.",
        source_snapshot_ids=["snapshot_demo_market_01", "snapshot_demo_team_01"],
    )


@router.get("/api/v1/fantasy/assets")
def fantasy_assets(eventId: str | None = None, assetType: str | None = None) -> dict[str, object]:
    state = get_state()
    items = state.assets
    if eventId and eventId != state.current_event_id:
        items = []
    if assetType:
        items = [asset for asset in items if asset.asset_type == assetType]
    return {"items": items}


@router.get("/api/v1/fantasy/teams/current")
def current_teams() -> dict[str, object]:
    return {"items": [get_state().team]}


@router.get("/api/v1/races")
def races(season: int | None = None) -> dict[str, object]:
    meetings = [RaceMeeting.model_validate(item) for item in get_state().race_data["items"]]
    if season:
        meetings = [meeting for meeting in meetings if meeting.season == season]
    return {"items": meetings}


@router.get("/api/v1/races/current")
def current_race() -> RaceMeeting:
    return RaceMeeting.model_validate(get_state().race_data["items"][0])


@router.get("/api/v1/races/{meeting_key}/sessions")
def sessions(meeting_key: str) -> dict[str, object]:
    items = [
        RaceSession.model_validate(item)
        for item in get_state().race_data["sessions"]
        if item["meetingKey"] == meeting_key
    ]
    return {"items": items}


@router.get("/api/v1/races/{meeting_key}/intelligence")
def intelligence(meeting_key: str) -> RaceWeekIntelligence:
    state = get_state()
    meeting = next(
        (item for item in state.race_data["items"] if item["meetingKey"] == meeting_key),
        None,
    )
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return RaceWeekIntelligence(
        meeting=RaceMeeting.model_validate(meeting),
        sessions=[
            RaceSession.model_validate(item)
            for item in state.race_data["sessions"]
            if item["meetingKey"] == meeting_key
        ],
        weather=state.race_data["weather"],
        race_control=state.race_data["raceControl"],
        news=state.news,
    )


@router.post("/api/v1/projections/run", status_code=status.HTTP_201_CREATED)
def projections_run(payload: dict[str, object]) -> ProjectionRunResult:
    event_id = str(payload.get("eventId") or get_state().current_event_id)
    state = get_state()
    result = run_projection(state.assets, event_id=event_id, stale_sources=state.is_degraded())
    state.projection_runs[result.projection_run_id] = result
    return result


@router.get("/api/v1/projections/runs/{projection_run_id}")
def projection_run(projection_run_id: str) -> ProjectionRunResult:
    state = get_state()
    if projection_run_id not in state.projection_runs:
        raise HTTPException(status_code=404, detail="Projection run not found")
    return state.projection_runs[projection_run_id]


@router.post("/api/v1/optimizer/recommendations", status_code=status.HTTP_201_CREATED)
def recommendations(request: OptimizerRequest) -> RecommendationRunResult:
    state = get_state()
    projection_run = (
        state.projection_runs.get(request.projection_run_id)
        if request.projection_run_id
        else run_projection(
            state.assets,
            event_id=request.event_id,
            stale_sources=state.is_degraded(),
        )
    )
    if projection_run is None:
        raise HTTPException(status_code=404, detail="Projection run not found")
    state.projection_runs[projection_run.projection_run_id] = projection_run
    result = optimize_recommendations(
        team=state.team,
        assets=state.assets,
        projections=projection_run.projections,
        event_id=request.event_id,
        strategy_mode=request.strategy_mode,
        locked_asset_ids=request.locked_asset_ids,
        banned_asset_ids=request.banned_asset_ids,
        allowed_chips=request.allowed_chips,
        max_options=request.max_options,
        projection_run_id=projection_run.projection_run_id,
        source_snapshot_ids=projection_run.source_snapshot_ids,
        degraded_sources=state.is_degraded(),
    )
    state.recommendation_runs[result.recommendation_run_id] = result
    return result


@router.get("/api/v1/recommendations/runs/{recommendation_run_id}")
def recommendation_run(recommendation_run_id: str) -> RecommendationRunResult:
    state = get_state()
    if recommendation_run_id not in state.recommendation_runs:
        raise HTTPException(status_code=404, detail="Recommendation run not found")
    return state.recommendation_runs[recommendation_run_id]


@router.post("/api/v1/leagues/import", status_code=status.HTTP_201_CREATED)
def import_league(request: LeagueImportRequest) -> ImportResult:
    state = get_state()
    state.league = request.model_dump(by_alias=True)
    return ImportResult(
        status="imported",
        item_count=len(request.rivals),
        source_snapshot_id="snapshot_manual_league",
        message="League snapshot imported for local analysis.",
    )


@router.get("/api/v1/leagues/{league_id}/analysis")
def league_analysis(league_id: str) -> LeagueAnalysis:
    analysis = analyze_league()
    if analysis.league_id != league_id:
        raise HTTPException(status_code=404, detail="League not found")
    return analysis


@router.post("/api/v1/agent/conversations", status_code=status.HTTP_201_CREATED)
def create_conversation() -> AgentConversation:
    now = utc_now()
    return AgentConversation(
        conversation_id="conv_demo",
        title="Demo Strategy Chat",
        created_at=now,
        updated_at=now,
        messages=[],
    )


@router.get("/api/v1/agent/conversations/{conversation_id}")
def get_conversation(conversation_id: str) -> AgentConversation:
    now = utc_now()
    return AgentConversation(
        conversation_id=conversation_id,
        title="Demo Strategy Chat",
        created_at=now,
        updated_at=now,
        messages=[],
    )


@router.post("/api/v1/agent/chat")
def chat(request: AgentChatRequest) -> AgentChatResponse:
    return answer_chat(request)
