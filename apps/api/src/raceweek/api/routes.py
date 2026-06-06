from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from raceweek import __version__
from raceweek.agents import answer_chat
from raceweek.api.data_first_routes import router as data_first_router
from raceweek.api.import_routes import router as import_router
from raceweek.core.models import (
    AgentChatRequest,
    AgentChatResponse,
    AgentConversation,
    FantasyAsset,
    FantasyTeamSnapshot,
    LeagueAnalysis,
    OptimizerRequest,
    ProjectionRunResult,
    ProviderTestRequest,
    ProviderTestResponse,
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
from raceweek.providers.adapters import ProviderError
from raceweek.providers.registry import provider_registry
from raceweek.storage.demo import (
    REPOSITORY,
    analyze_league,
    find_projection_run,
    find_recommendation_run,
    get_state,
    provider_configs,
    reset_state,
    save_projection_result,
    save_recommendation_result,
    simulate_openf1_failure,
)

router = APIRouter()
router.include_router(data_first_router)
router.include_router(import_router)


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
        "currentEventId": REPOSITORY.get_json_setting("current_event_id", state.current_event_id),
    }


@router.get("/api/v1/data-sources/status")
def data_source_status() -> dict[str, object]:
    return {"items": list(get_state().data_sources.values())}


@router.get("/api/v1/providers")
def providers() -> dict[str, object]:
    return {"items": provider_configs()}


@router.post("/api/v1/providers/test")
def provider_test(payload: ProviderTestRequest) -> ProviderTestResponse:
    try:
        return provider_registry().test_provider(payload.provider_name, model=payload.model)
    except ProviderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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


@router.get("/api/v1/fantasy/scores")
def fantasy_scores(eventId: str | None = None, assetId: str | None = None) -> dict[str, object]:
    items = get_state().scores
    if eventId:
        items = [score for score in items if score.event_id == eventId]
    if assetId:
        items = [score for score in items if score.asset_id == assetId]
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
    result = run_projection(
        _assets_for_strategy(event_id),
        event_id=event_id,
        stale_sources=state.is_degraded(),
    )
    save_projection_result(result)
    return result


@router.get("/api/v1/projections/runs/{projection_run_id}")
def projection_run(projection_run_id: str) -> ProjectionRunResult:
    result = find_projection_run(projection_run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Projection run not found")
    return result


@router.post("/api/v1/optimizer/recommendations", status_code=status.HTTP_201_CREATED)
def recommendations(request: OptimizerRequest) -> RecommendationRunResult:
    _ensure_optimizer_ready_for_real_data()
    state = get_state()
    assets = _assets_for_strategy(request.event_id)
    team = _team_for_strategy(request.team_snapshot_id)
    projection_run = (
        find_projection_run(request.projection_run_id)
        if request.projection_run_id
        else run_projection(
            assets,
            event_id=request.event_id,
            stale_sources=state.is_degraded(),
        )
    )
    if projection_run is None:
        raise HTTPException(status_code=404, detail="Projection run not found")
    save_projection_result(projection_run)
    result = optimize_recommendations(
        team=team,
        assets=assets,
        projections=projection_run.projections,
        event_id=request.event_id,
        strategy_mode=request.strategy_mode,
        locked_asset_ids=request.locked_asset_ids,
        banned_asset_ids=request.banned_asset_ids,
        allowed_chips=request.allowed_chips,
        custom_weights=request.custom_weights,
        idempotency_key=request.idempotency_key,
        max_options=request.max_options,
        projection_run_id=projection_run.projection_run_id,
        source_snapshot_ids=projection_run.source_snapshot_ids,
        degraded_sources=state.is_degraded(),
    )
    save_recommendation_result(result)
    return result


def _assets_for_strategy(event_id: str) -> list[FantasyAsset]:
    real_assets = REPOSITORY.real_assets()
    if real_assets:
        return real_assets
    if _real_data_mode_enabled():
        raise _optimizer_readiness_exception([_market_readiness_blocker()])
    state = get_state()
    if event_id == state.current_event_id or event_id.startswith("event_demo"):
        return state.assets
    raise HTTPException(
        status_code=409,
        detail="Load real fantasy market data before strategy runs.",
    )


def _team_for_strategy(team_snapshot_id: str) -> FantasyTeamSnapshot:
    real_teams = REPOSITORY.real_teams()
    if real_teams:
        team = next(
            (item for item in real_teams if item.team_snapshot_id == team_snapshot_id),
            None,
        )
        if team is None:
            raise HTTPException(status_code=404, detail="Real team snapshot not found.")
        return team
    if _real_data_mode_enabled():
        raise _optimizer_readiness_exception([_team_readiness_blocker()])
    state = get_state()
    if team_snapshot_id == state.team.team_snapshot_id or team_snapshot_id.startswith("team_demo"):
        return state.team
    raise HTTPException(status_code=409, detail="Select current teams before strategy runs.")


def _ensure_optimizer_ready_for_real_data() -> None:
    if not _real_data_mode_enabled():
        return
    blockers = _optimizer_readiness_blockers()
    if blockers:
        raise _optimizer_readiness_exception(blockers)


def _real_data_mode_enabled() -> bool:
    return str(REPOSITORY.get_json_setting("data_mode", "")) == "real"


def _optimizer_readiness_blockers() -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    if not REPOSITORY.real_assets():
        blockers.append(_market_readiness_blocker())
    if not REPOSITORY.real_teams():
        blockers.append(_team_readiness_blocker())
    return blockers


def _market_readiness_blocker() -> dict[str, str]:
    return {
        "key": "fantasy.market",
        "action": "sync_fantasy_game",
        "message": "Load real fantasy market/catalog data before running optimizer.",
    }


def _team_readiness_blocker() -> dict[str, str]:
    return {
        "key": "fantasy.user_team",
        "action": "open_team_selector",
        "message": "Select or import a current fantasy team before running optimizer.",
    }


def _optimizer_readiness_exception(blockers: list[dict[str, str]]) -> HTTPException:
    return HTTPException(
        status_code=409,
        detail={
            "code": "optimizer_readiness_blocked",
            "message": "Optimizer requires real fantasy market and current team data.",
            "blockers": blockers,
        },
    )


@router.get("/api/v1/recommendations/runs/{recommendation_run_id}")
def recommendation_run(recommendation_run_id: str) -> RecommendationRunResult:
    result = find_recommendation_run(recommendation_run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Recommendation run not found")
    return result


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
