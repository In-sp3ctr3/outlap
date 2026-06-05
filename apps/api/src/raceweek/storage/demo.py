from __future__ import annotations

from raceweek.core.models import (
    FantasyAsset,
    FantasyAssetScore,
    FantasyTeamSnapshot,
    LeagueAnalysis,
    ProjectionRunResult,
    ProviderConfig,
    RecommendationRunResult,
)
from raceweek.settings import settings
from raceweek.storage.fixtures import (
    DemoState,
    analyze_league_state,
)
from raceweek.storage.fixtures import (
    seed_demo_state as build_demo_state,
)
from raceweek.storage.repository import DuckDbRepository

REPOSITORY = DuckDbRepository(settings.database_path)
STATE = REPOSITORY.load_state()


def get_state() -> DemoState:
    return STATE


def _reload_state() -> DemoState:
    global STATE
    STATE = REPOSITORY.load_state()
    return STATE


def reset_state() -> DemoState:
    global STATE
    STATE = REPOSITORY.reset_demo()
    return STATE


def seed_demo_state() -> DemoState:
    return build_demo_state()


def replace_team(team: FantasyTeamSnapshot) -> None:
    REPOSITORY.save_team(team)
    _reload_state()


def replace_assets(event_id: str, assets: list[FantasyAsset]) -> None:
    REPOSITORY.save_assets(event_id, assets)
    _reload_state()


def replace_scores(event_id: str, scores: list[FantasyAssetScore]) -> None:
    REPOSITORY.save_scores(event_id, scores)
    _reload_state()


def replace_league(league: dict[str, object]) -> None:
    REPOSITORY.save_league(league)
    _reload_state()


def record_source_snapshot(
    snapshot_id: str,
    payload: dict[str, object],
    *,
    request_url_template: str,
) -> None:
    REPOSITORY.save_source_snapshot(
        snapshot_id,
        payload,
        request_url_template=request_url_template,
    )


def simulate_openf1_failure() -> None:
    previous = get_state().data_sources["openf1"]
    status = previous.model_copy(
        update={
            "status": "degraded",
            "severity": "warning",
            "message": "OpenF1 demo connector unavailable; using latest local snapshot.",
            "freshness": "stale",
            "action_required": "Retry sync or continue with manual/demo data.",
        }
    )
    REPOSITORY.save_data_source_status(status)
    _reload_state()


def provider_configs() -> list[ProviderConfig]:
    return REPOSITORY.load_provider_configs()


def save_projection_result(run: ProjectionRunResult) -> None:
    REPOSITORY.save_projection_run(run)
    _reload_state()


def find_projection_run(projection_run_id: str) -> ProjectionRunResult | None:
    try:
        return REPOSITORY.get_projection_run(projection_run_id)
    except KeyError:
        return None


def save_recommendation_result(run: RecommendationRunResult) -> None:
    REPOSITORY.save_recommendation_run(run)
    _reload_state()


def find_recommendation_run(recommendation_run_id: str) -> RecommendationRunResult | None:
    try:
        return REPOSITORY.get_recommendation_run(recommendation_run_id)
    except KeyError:
        return None


def analyze_league() -> LeagueAnalysis:
    return analyze_league_state(get_state())
