from __future__ import annotations

from raceweek.core.models import FantasyAsset, Projection, ProjectionRunResult, utc_now

MODEL_NAME = "transparent_weighted_demo"
MODEL_VERSION = "2026.1"


def run_projection(
    assets: list[FantasyAsset],
    *,
    event_id: str,
    stale_sources: bool = False,
) -> ProjectionRunResult:
    source_snapshot_ids = sorted(
        {
            asset.source_snapshot_id
            for asset in assets
            if asset.source_snapshot_id is not None
        }
    )
    warnings: list[str] = []
    if stale_sources:
        warnings.append("Some source data is degraded; confidence was reduced.")

    projections = [
        _project_asset(asset, stale_sources=stale_sources)
        for asset in sorted(assets, key=lambda item: item.asset_id)
    ]

    return ProjectionRunResult(
        projection_run_id=f"projrun_{event_id}_demo",
        event_id=event_id,
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
        generated_at=utc_now(),
        source_snapshot_ids=source_snapshot_ids or ["snapshot_demo_market_01"],
        projections=projections,
        status="degraded" if stale_sources else "ok",
        warnings=warnings,
    )


def _project_asset(asset: FantasyAsset, *, stale_sources: bool) -> Projection:
    recent = float(asset.fantasy_points or 0)
    ownership = float(asset.ownership_pct or 0)
    risk = float(asset.risk_score if asset.risk_score is not None else 0.35)
    value_signal = recent / max(asset.price_millions, 1)
    differential = (100 - ownership) / 100
    expected = round(
        (recent * 0.72)
        + (value_signal * 2.2)
        + (differential * 3.0)
        - (risk * 2.0),
        2,
    )
    expected = max(0, expected)
    confidence = max(0.35, min(0.92, 0.82 - (risk * 0.25) - (0.12 if stale_sources else 0)))
    floor = round(max(0, expected * (0.62 - risk * 0.12)), 2)
    ceiling = round(expected * (1.28 + (1 - ownership / 100) * 0.12), 2)
    price_delta = round((value_signal - 1.7) * 0.08, 2)
    contribution_breakdown = {
        "recentForm": round(recent * 0.72, 2),
        "valueSignal": round(value_signal * 2.2, 2),
        "differential": round(differential * 3.0, 2),
        "riskAdjustment": round(-(risk * 2.0), 2),
    }
    assumptions = ["Synthetic fixture projection; no live provider data used."]
    if stale_sources:
        assumptions.append("Confidence reduced because at least one source is degraded.")

    return Projection(
        asset_id=asset.asset_id,
        expected_points=expected,
        floor_points=floor,
        ceiling_points=ceiling,
        confidence=round(confidence, 2),
        risk_score=round(risk, 2),
        projected_price_delta_millions=price_delta,
        contribution_breakdown=contribution_breakdown,
        assumptions=assumptions,
        source_snapshot_id=asset.source_snapshot_id,
    )
