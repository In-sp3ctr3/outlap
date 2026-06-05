from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


class RaceweekModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )


AssetType = Literal["driver", "constructor"]
ChipAction = Literal[
    "none",
    "wildcard",
    "limitless",
    "no_negative",
    "autopilot",
    "3x_boost",
    "final_fix",
]
StrategyMode = Literal[
    "safe",
    "balanced",
    "aggressive",
    "budget_builder",
    "differential",
    "chip_optimized",
    "custom",
]
DataStatus = Literal["ok", "stale", "degraded", "error", "disabled", "unknown"]


class FantasyAsset(RaceweekModel):
    asset_id: str
    asset_type: AssetType
    display_name: str
    price_millions: float = Field(ge=0)
    external_id: str | None = None
    short_name: str | None = None
    constructor_name: str | None = None
    fantasy_points: float | None = None
    ownership_pct: float | None = Field(default=None, ge=0, le=100)
    selected_by_pct: float | None = Field(default=None, ge=0, le=100)
    points_per_million: float | None = None
    risk_score: float | None = Field(default=None, ge=0, le=1)
    source_snapshot_id: str | None = None


class FantasyAssetScore(RaceweekModel):
    asset_id: str
    event_id: str
    fantasy_points: float | None = None
    ownership_pct: float | None = Field(default=None, ge=0, le=100)
    selected_by_pct: float | None = Field(default=None, ge=0, le=100)
    captured_at: datetime
    source_snapshot_id: str | None = None


class TeamAsset(RaceweekModel):
    asset_id: str
    asset_type: AssetType
    boost_multiplier: float = 1


class ChipState(RaceweekModel):
    chip_name: str
    status: Literal["available", "used", "active", "unavailable", "unknown"]
    used_event_id: str | None = None


class FantasyTeamSnapshot(RaceweekModel):
    team_snapshot_id: str
    team_name: str
    event_id: str
    cost_cap_millions: float = Field(ge=0)
    budget_used_millions: float = Field(ge=0)
    budget_remaining_millions: float
    free_transfers: int = Field(ge=0)
    assets: list[TeamAsset] = Field(min_length=7, max_length=7)
    chips: list[ChipState]
    captured_at: datetime
    slot: int | None = Field(default=None, ge=1, le=3)
    transfer_penalty_points: float = Field(default=10, ge=0)
    source_snapshot_id: str | None = None

    @property
    def asset_ids(self) -> set[str]:
        return {asset.asset_id for asset in self.assets}


class LineupValidation(RaceweekModel):
    budget_used_millions: float
    budget_remaining_millions: float
    driver_count: int
    constructor_count: int


class Projection(RaceweekModel):
    asset_id: str
    expected_points: float
    confidence: float = Field(ge=0, le=1)
    risk_score: float = Field(ge=0, le=1)
    floor_points: float | None = None
    ceiling_points: float | None = None
    projected_price_delta_millions: float | None = None
    contribution_breakdown: dict[str, float] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)
    source_snapshot_id: str | None = None


class ProjectionRunResult(RaceweekModel):
    projection_run_id: str
    event_id: str
    model_name: str
    model_version: str
    generated_at: datetime
    source_snapshot_ids: list[str]
    projections: list[Projection]
    status: Literal["ok", "degraded", "error"] = "ok"
    warnings: list[str] = Field(default_factory=list)


class ProjectionBacktestResult(RaceweekModel):
    event_id: str
    model_name: str
    model_version: str
    generated_at: datetime
    sample_count: int = Field(ge=0)
    mean_absolute_error: float
    worst_asset_id: str | None = None
    warnings: list[str] = Field(default_factory=list)


class OptimizerRequest(RaceweekModel):
    team_snapshot_id: str
    event_id: str
    strategy_mode: StrategyMode
    projection_run_id: str | None = None
    locked_asset_ids: list[str] = Field(default_factory=list)
    banned_asset_ids: list[str] = Field(default_factory=list)
    allowed_chips: list[str] = Field(default_factory=list)
    custom_weights: dict[str, float] = Field(default_factory=dict)
    max_options: int = Field(default=20, ge=1, le=100)
    idempotency_key: str | None = None


class OptimizerRequestContext(RaceweekModel):
    team_snapshot_id: str = ""
    event_id: str = ""
    projection_run_id: str = ""
    strategy_mode: StrategyMode = "balanced"
    locked_asset_ids: list[str] = Field(default_factory=list)
    banned_asset_ids: list[str] = Field(default_factory=list)
    allowed_chips: list[str] = Field(default_factory=list)
    custom_weights: dict[str, float] = Field(default_factory=dict)
    max_options: int = Field(default=20, ge=1, le=100)
    idempotency_key_hash: str | None = None


class RecommendationTransfer(RaceweekModel):
    asset_out_id: str | None = None
    asset_in_id: str | None = None
    reason: str | None = None


class RecommendationOption(RaceweekModel):
    option_id: str
    rank: int = Field(ge=1)
    strategy_mode: StrategyMode
    expected_gross_points: float
    transfer_penalty_points: float
    expected_net_points: float
    budget_used_millions: float
    budget_remaining_millions: float
    risk_score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    summary: str
    transfers: list[RecommendationTransfer]
    chip_action: str | None = None
    expected_budget_delta_millions: float | None = None
    rationale: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    selected_asset_ids: list[str] = Field(default_factory=list)
    source_snapshot_ids: list[str] = Field(default_factory=list)
    projection_run_id: str
    ruleset_version: str = "fantasy_demo_2026_v1"
    optimizer_version: str = "bruteforce_demo_v1"


class RecommendationRunResult(RaceweekModel):
    recommendation_run_id: str
    team_snapshot_id: str
    event_id: str
    projection_run_id: str
    strategy_mode: StrategyMode
    generated_at: datetime
    status: Literal["ok", "degraded", "error"]
    options: list[RecommendationOption]
    warnings: list[str] = Field(default_factory=list)
    request_fingerprint: str = ""
    request_context: OptimizerRequestContext = Field(default_factory=OptimizerRequestContext)


class DataSourceStatus(RaceweekModel):
    source: str
    status: DataStatus
    severity: Literal["info", "warning", "error"]
    message: str
    last_successful_sync_at: datetime | None = None
    freshness: str
    connector_version: str
    license_note: str
    action_required: str | None = None


class ProviderConfig(RaceweekModel):
    provider_name: str
    display_name: str
    enabled: bool
    base_url: str | None = None
    default_model: str | None = None
    api_key_env_var: str | None = None
    supports_streaming: bool = True
    supports_tools: bool = False
    key_configured: bool = False


class ProviderTestRequest(RaceweekModel):
    provider_name: str
    model: str | None = None


class ProviderTestResponse(RaceweekModel):
    ok: bool
    provider_name: str
    message: str
    latency_ms: int | None = None


class ImportResult(RaceweekModel):
    status: Literal["imported", "updated"]
    item_count: int
    source_snapshot_id: str
    message: str
    warnings: list[str] = Field(default_factory=list)


class SyncRequest(RaceweekModel):
    simulate_failure: bool = False
    source: str | None = None


class SyncResult(RaceweekModel):
    status: Literal["ok", "degraded"]
    message: str
    source_snapshot_ids: list[str]


class RaceMeeting(RaceweekModel):
    meeting_key: str
    event_id: str
    season: int
    round_number: int
    meeting_name: str
    circuit_name: str
    country_name: str
    location: str
    date_start: datetime
    date_end: datetime
    locks_at: datetime
    status: str


class RaceSession(RaceweekModel):
    session_key: str
    meeting_key: str
    session_name: str
    session_type: str
    starts_at: datetime
    ends_at: datetime
    status: str


class RaceWeekIntelligence(RaceweekModel):
    meeting: RaceMeeting
    sessions: list[RaceSession]
    weather: list[dict[str, Any]]
    race_control: list[dict[str, Any]]
    news: list[dict[str, Any]]


class LeagueImportRequest(RaceweekModel):
    league_id: str
    event_id: str
    name: str | None = None
    rivals: list[dict[str, Any]]


class LeagueAnalysis(RaceweekModel):
    league_id: str
    summary: str
    user_rank: int | None = None
    gap_to_leader: int | None = None
    common_asset_ids: list[str] = Field(default_factory=list)
    differential_asset_ids: list[str] = Field(default_factory=list)
    catch_up_plan: list[str] = Field(default_factory=list)


class AgentConversation(RaceweekModel):
    conversation_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[dict[str, str]] = Field(default_factory=list)


class AgentChatRequest(RaceweekModel):
    conversation_id: str | None = None
    provider_name: str = "fake"
    message: str
    recommendation_run_id: str | None = None


class AgentChatResponse(RaceweekModel):
    conversation_id: str
    message: str
    status: Literal["ok", "fallback"]
    provider_name: str
    cited_recommendation_run_id: str | None = None
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    can_mutate_fantasy_account: bool = False


def utc_now() -> datetime:
    return datetime.now(UTC)
