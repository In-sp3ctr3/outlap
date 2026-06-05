from __future__ import annotations

from raceweek.core.models import RecommendationOption
from raceweek.core.strategy import weights_for


def rank_options(
    options: list[RecommendationOption],
    *,
    custom_weights: dict[str, float] | None = None,
) -> list[RecommendationOption]:
    return sorted(
        options,
        key=lambda option: (
            -_objective_score(option, custom_weights=custom_weights),
            -option.expected_net_points,
            option.risk_score,
            -option.confidence,
            -option.budget_remaining_millions,
            len([transfer for transfer in option.transfers if transfer.asset_in_id]),
            ",".join(option.selected_asset_ids),
        ),
    )


def _objective_score(
    option: RecommendationOption,
    *,
    custom_weights: dict[str, float] | None,
) -> float:
    weights = weights_for(option.strategy_mode, custom_weights=custom_weights)
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
