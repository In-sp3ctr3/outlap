from __future__ import annotations

from raceweek.core.models import (
    FantasyAsset,
    FantasyTeamSnapshot,
    Projection,
    RecommendationOption,
    RecommendationRunResult,
    StrategyMode,
    utc_now,
)
from raceweek.core.optimizer_bruteforce import solve_lineups_with_bruteforce
from raceweek.core.optimizer_options import build_recommendation_option
from raceweek.core.optimizer_ortools import (
    ORTOOLS_OPTIMIZER_VERSION,
    solve_lineups_with_ortools,
)
from raceweek.core.optimizer_requests import (
    build_request_context,
    fingerprint_request_context,
)
from raceweek.core.optimizer_scoring import rank_options
from raceweek.core.rules import (
    InvalidLineup,
    calculate_net_transfers,
    calculate_transfer_penalty,
    validate_lineup,
)

BRUTEFORCE_OPTIMIZER_VERSION = "bruteforce_demo_v1"


def optimize_recommendations(
    *,
    team: FantasyTeamSnapshot,
    assets: list[FantasyAsset],
    projections: list[Projection],
    event_id: str,
    strategy_mode: StrategyMode,
    locked_asset_ids: list[str],
    banned_asset_ids: list[str],
    allowed_chips: list[str],
    custom_weights: dict[str, float] | None = None,
    idempotency_key: str | None = None,
    max_options: int,
    projection_run_id: str,
    source_snapshot_ids: list[str],
    degraded_sources: bool = False,
) -> RecommendationRunResult:
    request_context = build_request_context(
        team_snapshot_id=team.team_snapshot_id,
        event_id=event_id,
        projection_run_id=projection_run_id,
        strategy_mode=strategy_mode,
        locked_asset_ids=locked_asset_ids,
        banned_asset_ids=banned_asset_ids,
        allowed_chips=allowed_chips,
        custom_weights=custom_weights,
        max_options=max_options,
        idempotency_key=idempotency_key,
    )
    request_fingerprint = fingerprint_request_context(request_context)
    options: list[RecommendationOption] = []
    chip_actions = _chip_actions(strategy_mode, request_context.allowed_chips)
    for chip_action in chip_actions:
        options.extend(
            _optimize_for_chip(
                team=team,
                assets=assets,
                projections=projections,
                strategy_mode=strategy_mode,
                locked_asset_ids=set(request_context.locked_asset_ids),
                banned_asset_ids=set(request_context.banned_asset_ids),
                custom_weights=request_context.custom_weights,
                request_fingerprint=request_fingerprint,
                max_options=max_options,
                projection_run_id=projection_run_id,
                source_snapshot_ids=source_snapshot_ids,
                chip_action=chip_action,
                degraded_sources=degraded_sources,
            )
    )

    options = rank_options(options, custom_weights=request_context.custom_weights)[:max_options]
    ranked = [
        option.model_copy(update={"rank": rank})
        for rank, option in enumerate(options, start=1)
    ]
    warnings = (
        ["One or more data sources are degraded; using latest local snapshot."]
        if degraded_sources
        else []
    )
    if not ranked:
        warnings.append("No legal lineup matched the selected constraints.")

    return RecommendationRunResult(
        recommendation_run_id=(
            f"recrun_{event_id}_{strategy_mode}_{request_fingerprint[:12]}"
        ),
        team_snapshot_id=team.team_snapshot_id,
        event_id=event_id,
        projection_run_id=projection_run_id,
        strategy_mode=strategy_mode,
        generated_at=utc_now(),
        status="degraded" if degraded_sources else "ok",
        options=ranked,
        warnings=warnings,
        request_fingerprint=request_fingerprint,
        request_context=request_context,
    )


def _chip_actions(strategy_mode: StrategyMode, allowed_chips: list[str]) -> list[str | None]:
    if strategy_mode == "chip_optimized" and allowed_chips:
        return [None, *allowed_chips]
    return [allowed_chips[0] if len(allowed_chips) == 1 else None]


def _optimize_for_chip(
    *,
    team: FantasyTeamSnapshot,
    assets: list[FantasyAsset],
    projections: list[Projection],
    strategy_mode: StrategyMode,
    locked_asset_ids: set[str],
    banned_asset_ids: set[str],
    custom_weights: dict[str, float],
    request_fingerprint: str,
    max_options: int,
    projection_run_id: str,
    source_snapshot_ids: list[str],
    chip_action: str | None,
    degraded_sources: bool,
) -> list[RecommendationOption]:
    projection_by_asset = {projection.asset_id: projection for projection in projections}
    asset_by_id = {asset.asset_id: asset for asset in assets}
    locked_assets = [
        asset_by_id[asset_id]
        for asset_id in locked_asset_ids
        if asset_id in asset_by_id
    ]
    candidates = [
        asset
        for asset in assets
        if asset.asset_id not in banned_asset_ids and asset.asset_id in projection_by_asset
    ]
    options: list[RecommendationOption] = []
    current_ids = team.asset_ids

    locked_candidate_ids = {asset.asset_id for asset in locked_assets}
    solver_lineups = solve_lineups_with_ortools(
        assets=candidates,
        projections=projection_by_asset,
        current_asset_ids=current_ids,
        locked_asset_ids=locked_candidate_ids,
        strategy_mode=strategy_mode,
        custom_weights=custom_weights,
        cost_cap_millions=team.cost_cap_millions,
        free_transfers=team.free_transfers,
        penalty_points=team.transfer_penalty_points,
        chip_action=chip_action,
        max_options=max_options,
    )
    for selected_ids in solver_lineups:
        option = _option_from_selected_ids(
            option_id=(
                f"recopt_{request_fingerprint[:8]}_{strategy_mode}_{chip_action or 'none'}_"
                f"{ORTOOLS_OPTIMIZER_VERSION}_{len(options) + 1}"
            ),
            team=team,
            asset_by_id=asset_by_id,
            projections=projection_by_asset,
            selected_ids=selected_ids,
            strategy_mode=strategy_mode,
            chip_action=chip_action,
            projection_run_id=projection_run_id,
            source_snapshot_ids=source_snapshot_ids,
            degraded_sources=degraded_sources,
            optimizer_version=ORTOOLS_OPTIMIZER_VERSION,
        )
        if option is not None:
            options.append(option)

    if options:
        return rank_options(options, custom_weights=custom_weights)[:max_options]

    for selected_ids in solve_lineups_with_bruteforce(
        assets=candidates,
        locked_asset_ids=locked_candidate_ids,
        cost_cap_millions=team.cost_cap_millions,
        chip_action=chip_action,
    ):
        option = _option_from_selected_ids(
            option_id=(
                f"recopt_{request_fingerprint[:8]}_{strategy_mode}_"
                f"{chip_action or 'none'}_{len(options) + 1}"
            ),
            team=team,
            asset_by_id=asset_by_id,
            projections=projection_by_asset,
            selected_ids=selected_ids,
            strategy_mode=strategy_mode,
            chip_action=chip_action,
            projection_run_id=projection_run_id,
            source_snapshot_ids=source_snapshot_ids,
            degraded_sources=degraded_sources,
            optimizer_version=BRUTEFORCE_OPTIMIZER_VERSION,
        )
        if option is not None:
            options.append(option)

    return rank_options(options, custom_weights=custom_weights)[: max(max_options, 10)]


def _option_from_selected_ids(
    *,
    option_id: str,
    team: FantasyTeamSnapshot,
    asset_by_id: dict[str, FantasyAsset],
    projections: dict[str, Projection],
    selected_ids: tuple[str, ...],
    strategy_mode: StrategyMode,
    chip_action: str | None,
    projection_run_id: str,
    source_snapshot_ids: list[str],
    degraded_sources: bool,
    optimizer_version: str,
) -> RecommendationOption | None:
    lineup = [asset_by_id[asset_id] for asset_id in selected_ids]
    try:
        validation = validate_lineup(
            lineup,
            cost_cap_millions=team.cost_cap_millions,
            chip_action=chip_action,
        )
    except InvalidLineup:
        return None
    penalty = calculate_transfer_penalty(
        calculate_net_transfers(team.asset_ids, set(selected_ids)),
        free_transfers=team.free_transfers,
        penalty_points=team.transfer_penalty_points,
        chip_action=chip_action,
    )
    return build_recommendation_option(
        option_id=option_id,
        strategy_mode=strategy_mode,
        lineup=lineup,
        selected_ids=selected_ids,
        projections=projections,
        current_ids=team.asset_ids,
        penalty=penalty,
        budget_used=validation.budget_used_millions,
        budget_remaining=validation.budget_remaining_millions,
        chip_action=chip_action,
        projection_run_id=projection_run_id,
        source_snapshot_ids=source_snapshot_ids,
        degraded_sources=degraded_sources,
        optimizer_version=optimizer_version,
    )
