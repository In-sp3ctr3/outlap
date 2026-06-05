from __future__ import annotations

from itertools import combinations

from raceweek.core.models import (
    FantasyAsset,
    FantasyTeamSnapshot,
    Projection,
    RecommendationOption,
    RecommendationRunResult,
    RecommendationTransfer,
    StrategyMode,
    utc_now,
)
from raceweek.core.rules import (
    InvalidLineup,
    calculate_net_transfers,
    calculate_transfer_penalty,
    validate_lineup,
)
from raceweek.core.strategy import weights_for


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
    max_options: int,
    projection_run_id: str,
    source_snapshot_ids: list[str],
    degraded_sources: bool = False,
) -> RecommendationRunResult:
    options: list[RecommendationOption] = []
    chip_actions = _chip_actions(strategy_mode, allowed_chips)
    for chip_action in chip_actions:
        options.extend(
            _optimize_for_chip(
                team=team,
                assets=assets,
                projections=projections,
                strategy_mode=strategy_mode,
                locked_asset_ids=set(locked_asset_ids),
                banned_asset_ids=set(banned_asset_ids),
                max_options=max_options,
                projection_run_id=projection_run_id,
                source_snapshot_ids=source_snapshot_ids,
                chip_action=chip_action,
                degraded_sources=degraded_sources,
            )
    )

    options = _rank_options(options)[:max_options]
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
        recommendation_run_id=f"recrun_{event_id}_{strategy_mode}_demo",
        team_snapshot_id=team.team_snapshot_id,
        event_id=event_id,
        projection_run_id=projection_run_id,
        strategy_mode=strategy_mode,
        generated_at=utc_now(),
        status="degraded" if degraded_sources else "ok",
        options=ranked,
        warnings=warnings,
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
    drivers = [asset for asset in candidates if asset.asset_type == "driver"]
    constructors = [asset for asset in candidates if asset.asset_type == "constructor"]
    options: list[RecommendationOption] = []
    current_ids = team.asset_ids

    locked_driver_ids = {asset.asset_id for asset in locked_assets if asset.asset_type == "driver"}
    locked_constructor_ids = {
        asset.asset_id
        for asset in locked_assets
        if asset.asset_type == "constructor"
    }

    for driver_combo in combinations(drivers, 5):
        driver_ids = {asset.asset_id for asset in driver_combo}
        if not locked_driver_ids <= driver_ids:
            continue
        for constructor_combo in combinations(constructors, 2):
            constructor_ids = {asset.asset_id for asset in constructor_combo}
            if not locked_constructor_ids <= constructor_ids:
                continue
            lineup = [*driver_combo, *constructor_combo]
            try:
                validation = validate_lineup(
                    lineup,
                    cost_cap_millions=team.cost_cap_millions,
                    chip_action=chip_action,
                )
            except InvalidLineup:
                continue
            selected_ids = tuple(sorted(asset.asset_id for asset in lineup))
            net_transfers = calculate_net_transfers(current_ids, set(selected_ids))
            penalty = calculate_transfer_penalty(
                net_transfers,
                free_transfers=team.free_transfers,
                penalty_points=team.transfer_penalty_points,
                chip_action=chip_action,
            )
            option = _build_option(
                option_id=f"recopt_{strategy_mode}_{chip_action or 'none'}_{len(options) + 1}",
                strategy_mode=strategy_mode,
                lineup=lineup,
                selected_ids=selected_ids,
                projections=projection_by_asset,
                current_ids=current_ids,
                penalty=penalty,
                budget_used=validation.budget_used_millions,
                budget_remaining=validation.budget_remaining_millions,
                chip_action=chip_action,
                projection_run_id=projection_run_id,
                source_snapshot_ids=source_snapshot_ids,
                degraded_sources=degraded_sources,
            )
            options.append(option)

    return _rank_options(options)[: max(max_options, 10)]


def _build_option(
    *,
    option_id: str,
    strategy_mode: StrategyMode,
    lineup: list[FantasyAsset],
    selected_ids: tuple[str, ...],
    projections: dict[str, Projection],
    current_ids: set[str],
    penalty: float,
    budget_used: float,
    budget_remaining: float,
    chip_action: str | None,
    projection_run_id: str,
    source_snapshot_ids: list[str],
    degraded_sources: bool,
    ) -> RecommendationOption:
    selected_projections = [projections[asset.asset_id] for asset in lineup]
    gross = round(sum(projection.expected_points for projection in selected_projections), 2)
    risk = round(
        sum(projection.risk_score for projection in selected_projections)
        / len(selected_projections),
        2,
    )
    confidence = round(
        sum(projection.confidence for projection in selected_projections)
        / len(selected_projections),
        2,
    )
    net = round(gross - penalty, 2)
    removed = sorted(current_ids - set(selected_ids))
    added = sorted(set(selected_ids) - current_ids)
    transfers = [
        RecommendationTransfer(
            asset_out_id=out_id,
            asset_in_id=in_id,
            reason="Higher deterministic net score under selected strategy.",
        )
        for out_id, in_id in zip(removed, added, strict=True)
    ]
    if not transfers:
        transfers = [RecommendationTransfer(reason="Hold current lineup; no transfer required.")]
    budget_delta = round(
        sum(
            projections[asset_id].projected_price_delta_millions or 0
            for asset_id in selected_ids
        ),
        2,
    )
    top_in = next((transfer.asset_in_id for transfer in transfers if transfer.asset_in_id), None)
    chip_label = chip_action or "none"
    warnings = []
    if degraded_sources:
        warnings.append("Data source degraded; recommendation uses latest local snapshot.")
    if chip_action == "limitless":
        warnings.append(
            "Limitless ignores this event budget cap; future team reversion remains manual."
        )

    return RecommendationOption(
        option_id=option_id,
        rank=1,
        strategy_mode=strategy_mode,
        chip_action=chip_action,
        expected_gross_points=gross,
        transfer_penalty_points=penalty,
        expected_net_points=net,
        budget_used_millions=budget_used,
        budget_remaining_millions=budget_remaining,
        expected_budget_delta_millions=budget_delta,
        risk_score=risk,
        confidence=confidence,
        summary=_summary(top_in, chip_label, net),
        transfers=transfers,
        rationale=[
            (
                "Rules engine validated 5 drivers, 2 constructors, duplicate prevention, "
                "and budget constraints."
            ),
            "Net score subtracts transfer penalties before ranking.",
            "The AI layer receives this option only as explanation context.",
        ],
        assumptions=[
            "Manual application required on the fantasy platform.",
            "Synthetic demo projections stand in for live connector snapshots.",
        ],
        warnings=warnings,
        selected_asset_ids=list(selected_ids),
        source_snapshot_ids=source_snapshot_ids,
        projection_run_id=projection_run_id,
    )


def _summary(top_in: str | None, chip_label: str, net_points: float) -> str:
    if top_in:
        return (
            f"Recommend bringing in {top_in} with chip scenario {chip_label}; "
            f"net {net_points:.1f} pts."
        )
    return f"Hold lineup with chip scenario {chip_label}; net {net_points:.1f} pts."


def _rank_options(options: list[RecommendationOption]) -> list[RecommendationOption]:
    return sorted(
        options,
        key=lambda option: (
            -_objective_score(option),
            -option.expected_net_points,
            option.risk_score,
            -option.confidence,
            -option.budget_remaining_millions,
            len([transfer for transfer in option.transfers if transfer.asset_in_id]),
            ",".join(option.selected_asset_ids),
        ),
    )


def _objective_score(option: RecommendationOption) -> float:
    weights = weights_for(option.strategy_mode)
    ceiling_proxy = option.expected_gross_points * (1.15 - option.risk_score * 0.1)
    floor_proxy = option.expected_gross_points * (0.72 - option.risk_score * 0.12)
    differential_proxy = sum(
        1
        for asset_id in option.selected_asset_ids
        if asset_id.endswith(("foxtrot", "juliet", "four"))
    )
    return (
        option.expected_net_points * weights["expected"]
        + floor_proxy * weights["floor"]
        + ceiling_proxy * weights["ceiling"]
        - option.risk_score * 20 * weights["riskPenalty"]
        + (option.expected_budget_delta_millions or 0) * 10 * weights["budgetGrowth"]
        + differential_proxy * weights["differential"]
    )
