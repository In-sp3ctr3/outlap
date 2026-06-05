from __future__ import annotations

from raceweek.core.chip_simulator import simulate_chip_scores
from raceweek.core.models import (
    FantasyAsset,
    Projection,
    RecommendationOption,
    RecommendationTransfer,
    StrategyMode,
)


def build_recommendation_option(
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
    optimizer_version: str,
    team_asset_boosts: dict[str, float],
) -> RecommendationOption:
    selected_projections = [projections[asset.asset_id] for asset in lineup]
    simulated_scores = simulate_chip_scores(
        lineup=lineup,
        projections=projections,
        team_asset_boosts=team_asset_boosts,
        chip_action=chip_action,
    )
    gross = round(sum(simulated_scores.values()), 2)
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
        summary=_summary(top_in, chip_action or "none", net),
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
        optimizer_version=optimizer_version,
    )


def _summary(top_in: str | None, chip_label: str, net_points: float) -> str:
    if top_in:
        return (
            f"Recommend bringing in {top_in} with chip scenario {chip_label}; "
            f"net {net_points:.1f} pts."
        )
    return f"Hold lineup with chip scenario {chip_label}; net {net_points:.1f} pts."
