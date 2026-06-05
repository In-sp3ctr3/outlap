from __future__ import annotations

from raceweek.core.projections import run_backtest, run_projection
from raceweek.storage.demo import seed_demo_state


def test_projection_contribution_breakdown_matches_expected_points() -> None:
    state = seed_demo_state()
    result = run_projection(state.assets, event_id=state.current_event_id)
    first = result.projections[0]

    assert set(first.contribution_breakdown) == {
        "recentForm",
        "valueSignal",
        "differential",
        "riskAdjustment",
    }
    assert abs(sum(first.contribution_breakdown.values()) - first.expected_points) <= 0.02


def test_stale_sources_reduce_projection_confidence() -> None:
    state = seed_demo_state()
    fresh = run_projection(state.assets, event_id=state.current_event_id)
    stale = run_projection(state.assets, event_id=state.current_event_id, stale_sources=True)

    assert stale.status == "degraded"
    assert stale.warnings
    assert stale.projections[0].confidence < fresh.projections[0].confidence


def test_backtest_compares_projection_to_actual_fixture_scores() -> None:
    state = seed_demo_state()

    result = run_backtest(state.assets, event_id=state.current_event_id)

    assert result.event_id == state.current_event_id
    assert result.sample_count == len(state.assets)
    assert result.mean_absolute_error > 0
    assert result.worst_asset_id
    assert result.model_name == "transparent_weighted_demo"
