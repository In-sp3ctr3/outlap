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
    source_snapshot_ids: set[str]
    projection_runs: dict[str, ProjectionRunResult] = field(default_factory=dict)
    recommendation_runs: dict[str, RecommendationRunResult] = field(default_factory=dict)

    def is_degraded(self) -> bool:
        return any(
            status.status in {"degraded", "error", "stale"}
            for status in self.data_sources.values()
        )


def load_fixture(name: str) -> dict[str, Any]:
    with (FIXTURES / name).open() as file:
        payload: dict[str, Any] = json.load(file)
    return payload


def seed_demo_state() -> DemoState:
    market = load_fixture("fantasy_market_demo.json")
    team = load_fixture("fantasy_team_demo.json")
    race_data = load_fixture("race_calendar_demo.json")
    news = load_fixture("news_demo.json")
    league = load_fixture("league_demo.json")
    now = utc_now()

    return DemoState(
        assets=[FantasyAsset.model_validate(asset) for asset in market["assets"]],
        team=FantasyTeamSnapshot.model_validate(team),
        current_event_id=market["eventId"],
        race_data=race_data,
        news=news["items"],
        league=league,
        source_snapshot_ids={
            "snapshot_demo_market_01",
            "snapshot_demo_team_01",
            "snapshot_demo_race_01",
            "snapshot_demo_news_01",
            "snapshot_demo_league_01",
        },
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
        ProviderConfig(provider_name="ollama", display_name="Ollama local", enabled=False),
        ProviderConfig(
            provider_name="openai",
            display_name="OpenAI",
            enabled=False,
            default_model="gpt-5.4",
            supports_tools=True,
        ),
        ProviderConfig(provider_name="anthropic", display_name="Anthropic Claude", enabled=False),
        ProviderConfig(provider_name="gemini", display_name="Google Gemini", enabled=False),
        ProviderConfig(provider_name="mistral", display_name="Mistral", enabled=False),
        ProviderConfig(provider_name="openrouter", display_name="OpenRouter", enabled=False),
        ProviderConfig(provider_name="groq", display_name="Groq", enabled=False),
        ProviderConfig(provider_name="xai", display_name="xAI", enabled=False),
        ProviderConfig(
            provider_name="custom-openai",
            display_name="Custom OpenAI-compatible",
            enabled=False,
            supports_tools=True,
        ),
    ]


def analyze_league_state(state: DemoState) -> LeagueAnalysis:
    user_assets = state.team.asset_ids
    rival_assets = [set(rival.get("assetIds", [])) for rival in state.league.get("rivals", [])]
    common: set[str] = set()
    for assets in rival_assets:
        common |= user_assets & assets
    rival_union = set().union(*rival_assets) if rival_assets else set()
    return LeagueAnalysis(
        league_id=state.league["leagueId"],
        summary=(
            "You are close enough for a controlled differential plan; prioritize one "
            "low-owned upgrade over chip panic."
        ),
        user_rank=state.league.get("userRank"),
        gap_to_leader=state.league.get("gapToLeader"),
        common_asset_ids=sorted(common),
        differential_asset_ids=sorted(user_assets - rival_union),
        catch_up_plan=[
            "Compare balanced and differential strategies before locking transfers.",
            "Use Driver Foxtrot-style low-owned value only if data health is fresh.",
            "Preserve chips unless the optimizer shows a clear net gain.",
        ],
    )
