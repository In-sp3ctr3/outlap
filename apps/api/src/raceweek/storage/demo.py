from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from raceweek.core.models import (
    DataSourceStatus,
    FantasyAsset,
    FantasyTeamSnapshot,
    LeagueAnalysis,
    ProjectionRunResult,
    ProviderConfig,
    RecommendationRunResult,
    utc_now,
)

ROOT = Path(__file__).resolve().parents[5]
FIXTURES = ROOT / "packages" / "fixtures"


@dataclass
class DemoState:
    assets: list[FantasyAsset]
    team: FantasyTeamSnapshot
    current_event_id: str
    race_data: dict[str, Any]
    news: list[dict[str, Any]]
    league: dict[str, Any]
    data_sources: dict[str, DataSourceStatus]
    projection_runs: dict[str, ProjectionRunResult] = field(default_factory=dict)
    recommendation_runs: dict[str, RecommendationRunResult] = field(default_factory=dict)

    def is_degraded(self) -> bool:
        return any(
            status.status in {"degraded", "error", "stale"}
            for status in self.data_sources.values()
        )


def _load_json(name: str) -> dict[str, Any]:
    with (FIXTURES / name).open() as file:
        payload: dict[str, Any] = json.load(file)
    return payload


def seed_demo_state() -> DemoState:
    market = _load_json("fantasy_market_demo.json")
    team = _load_json("fantasy_team_demo.json")
    race_data = _load_json("race_calendar_demo.json")
    news = _load_json("news_demo.json")
    league = _load_json("league_demo.json")
    now = utc_now()

    return DemoState(
        assets=[FantasyAsset.model_validate(asset) for asset in market["assets"]],
        team=FantasyTeamSnapshot.model_validate(team),
        current_event_id=market["eventId"],
        race_data=race_data,
        news=news["items"],
        league=league,
        data_sources={
            "manual_import": DataSourceStatus(
                source="manual_import",
                status="healthy",
                severity="info",
                message="Demo team and market fixtures loaded.",
                last_successful_sync_at=now,
                freshness="fresh",
                connector_version="manual-demo-v1",
                license_note="Synthetic fixture data",
            ),
            "openf1": DataSourceStatus(
                source="openf1",
                status="healthy",
                severity="info",
                message="Demo race-week intelligence loaded from local fixture.",
                last_successful_sync_at=now,
                freshness="fresh",
                connector_version="openf1-demo-v1",
                license_note="Synthetic fixture derived from public schema shape",
            ),
            "news": DataSourceStatus(
                source="news",
                status="healthy",
                severity="info",
                message="Demo news feed loaded.",
                last_successful_sync_at=now,
                freshness="fresh",
                connector_version="rss-demo-v1",
                license_note="Synthetic fixture data",
            ),
        },
    )


STATE = seed_demo_state()


def get_state() -> DemoState:
    return STATE


def reset_state() -> DemoState:
    global STATE
    STATE = seed_demo_state()
    return STATE


def replace_team(team: FantasyTeamSnapshot) -> None:
    STATE.team = team


def replace_assets(event_id: str, assets: list[FantasyAsset]) -> None:
    STATE.current_event_id = event_id
    STATE.assets = assets


def simulate_openf1_failure() -> None:
    previous = STATE.data_sources["openf1"]
    STATE.data_sources["openf1"] = previous.model_copy(
        update={
            "status": "degraded",
            "severity": "warning",
            "message": "OpenF1 demo connector unavailable; using latest local snapshot.",
            "freshness": "stale",
            "action_required": "Retry sync or continue with manual/demo data.",
        }
    )


def provider_configs() -> list[ProviderConfig]:
    return [
        ProviderConfig(
            provider_name="fake",
            display_name="Fake deterministic provider",
            enabled=True,
            default_model="fake-strategist",
            supports_tools=True,
            key_configured=True,
        ),
        ProviderConfig(
            provider_name="fake-fail",
            display_name="Fake failing provider",
            enabled=True,
            default_model="fake-failure",
            key_configured=True,
        ),
        ProviderConfig(
            provider_name="ollama",
            display_name="Ollama local",
            enabled=False,
            default_model="llama3.1",
        ),
        ProviderConfig(
            provider_name="openai",
            display_name="OpenAI",
            enabled=False,
            default_model="gpt-5.4",
            supports_tools=True,
        ),
        ProviderConfig(
            provider_name="anthropic",
            display_name="Anthropic Claude",
            enabled=False,
            default_model="claude-sonnet",
            supports_tools=True,
        ),
        ProviderConfig(
            provider_name="gemini",
            display_name="Google Gemini",
            enabled=False,
            default_model="gemini-pro",
            supports_tools=True,
        ),
        ProviderConfig(
            provider_name="mistral",
            display_name="Mistral",
            enabled=False,
            default_model="mistral-large",
        ),
        ProviderConfig(
            provider_name="openrouter",
            display_name="OpenRouter",
            enabled=False,
            default_model="auto",
            supports_tools=True,
        ),
        ProviderConfig(
            provider_name="groq",
            display_name="Groq",
            enabled=False,
            default_model="llama",
        ),
        ProviderConfig(
            provider_name="xai",
            display_name="xAI",
            enabled=False,
            default_model="grok",
            supports_tools=True,
        ),
        ProviderConfig(
            provider_name="custom-openai",
            display_name="Custom OpenAI-compatible",
            enabled=False,
            default_model="custom",
            supports_tools=True,
        ),
    ]


def analyze_league() -> LeagueAnalysis:
    user_assets = get_state().team.asset_ids
    rival_assets = [
        set(rival.get("assetIds", []))
        for rival in STATE.league.get("rivals", [])
    ]
    common: set[str] = set()
    for assets in rival_assets:
        common |= user_assets & assets
    rival_union = set().union(*rival_assets) if rival_assets else set()
    differentials = sorted(user_assets - rival_union)
    return LeagueAnalysis(
        league_id=STATE.league["leagueId"],
        summary=(
            "You are close enough for a controlled differential plan; prioritize one "
            "low-owned upgrade over chip panic."
        ),
        user_rank=STATE.league.get("userRank"),
        gap_to_leader=STATE.league.get("gapToLeader"),
        common_asset_ids=sorted(common),
        differential_asset_ids=differentials,
        catch_up_plan=[
            "Compare balanced and differential strategies before locking transfers.",
            "Use Driver Foxtrot-style low-owned value only if data health is fresh.",
            "Preserve chips unless the optimizer shows a clear net gain.",
        ],
    )
