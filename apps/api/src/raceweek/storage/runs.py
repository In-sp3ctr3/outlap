from __future__ import annotations

import duckdb

from raceweek.core.models import ProjectionRunResult, RecommendationRunResult
from raceweek.storage.jsonio import dump_json, load_json_value


def load_projection_runs(
    connection: duckdb.DuckDBPyConnection,
) -> dict[str, ProjectionRunResult]:
    rows = connection.execute(
        "SELECT payload_json FROM projection_runs WHERE payload_json IS NOT NULL"
    ).fetchall()
    runs = [ProjectionRunResult.model_validate(load_json_value(row[0])) for row in rows]
    return {run.projection_run_id: run for run in runs}


def load_recommendation_runs(
    connection: duckdb.DuckDBPyConnection,
) -> dict[str, RecommendationRunResult]:
    rows = connection.execute(
        "SELECT payload_json FROM recommendation_runs WHERE payload_json IS NOT NULL"
    ).fetchall()
    runs = [RecommendationRunResult.model_validate(load_json_value(row[0])) for row in rows]
    return {run.recommendation_run_id: run for run in runs}


def load_projection_run(
    connection: duckdb.DuckDBPyConnection,
    projection_run_id: str,
) -> ProjectionRunResult:
    row = connection.execute(
        "SELECT payload_json FROM projection_runs WHERE projection_run_id = ?",
        [projection_run_id],
    ).fetchone()
    if row is None:
        raise KeyError(projection_run_id)
    return ProjectionRunResult.model_validate(load_json_value(row[0]))


def load_recommendation_run(
    connection: duckdb.DuckDBPyConnection,
    recommendation_run_id: str,
) -> RecommendationRunResult:
    row = connection.execute(
        "SELECT payload_json FROM recommendation_runs WHERE recommendation_run_id = ?",
        [recommendation_run_id],
    ).fetchone()
    if row is None:
        raise KeyError(recommendation_run_id)
    return RecommendationRunResult.model_validate(load_json_value(row[0]))


def save_projection_run(
    connection: duckdb.DuckDBPyConnection,
    run: ProjectionRunResult,
) -> None:
    connection.execute(
        "DELETE FROM projections WHERE projection_run_id = ?",
        [run.projection_run_id],
    )
    connection.execute(
        "DELETE FROM projection_runs WHERE projection_run_id = ?",
        [run.projection_run_id],
    )
    connection.execute(
        """
        INSERT INTO projection_runs (
          projection_run_id, event_id, model_name, model_version,
          generated_at, source_snapshot_ids_json, config_json, status,
          error_message, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?::JSON, ?::JSON, ?, ?, ?::JSON)
        """,
        [
            run.projection_run_id,
            run.event_id,
            run.model_name,
            run.model_version,
            run.generated_at,
            dump_json(run.source_snapshot_ids),
            "{}",
            run.status,
            None,
            dump_json(run.model_dump(by_alias=True, mode="json")),
        ],
    )
    for projection in run.projections:
        connection.execute(
            """
            INSERT INTO projections (
              projection_id, projection_run_id, asset_id,
              expected_points, floor_points, ceiling_points,
              confidence, risk_score, projected_price_delta_millions,
              contribution_breakdown_json, assumptions_json, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?::JSON, ?::JSON, ?::JSON)
            """,
            [
                f"{run.projection_run_id}_{projection.asset_id}",
                run.projection_run_id,
                projection.asset_id,
                projection.expected_points,
                projection.floor_points,
                projection.ceiling_points,
                projection.confidence,
                projection.risk_score,
                projection.projected_price_delta_millions,
                dump_json(projection.contribution_breakdown),
                dump_json(projection.assumptions),
                dump_json(projection.model_dump(by_alias=True, mode="json")),
            ],
        )


def save_recommendation_run(
    connection: duckdb.DuckDBPyConnection,
    run: RecommendationRunResult,
) -> None:
    connection.execute(
        "DELETE FROM recommendation_options WHERE recommendation_run_id = ?",
        [run.recommendation_run_id],
    )
    connection.execute(
        "DELETE FROM recommendation_runs WHERE recommendation_run_id = ?",
        [run.recommendation_run_id],
    )
    connection.execute(
        """
        INSERT INTO recommendation_runs (
          recommendation_run_id, user_id, team_snapshot_id, event_id,
          projection_run_id, ruleset_version, optimizer_version,
          strategy_mode, request_json, generated_at, status,
          error_message, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?::JSON, ?, ?, ?, ?::JSON)
        """,
        [
            run.recommendation_run_id,
            "user_demo",
            run.team_snapshot_id,
            run.event_id,
            run.projection_run_id,
            "fantasy_demo_2026_v1",
            "bruteforce_demo_v1",
            run.strategy_mode,
            "{}",
            run.generated_at,
            run.status,
            None,
            dump_json(run.model_dump(by_alias=True, mode="json")),
        ],
    )
    for option in run.options:
        connection.execute(
            """
            INSERT INTO recommendation_options (
              option_id, recommendation_run_id, rank, strategy_mode,
              chip_action, expected_gross_points, transfer_penalty_points,
              expected_net_points, budget_used_millions,
              budget_remaining_millions, expected_budget_delta_millions,
              risk_score, confidence, summary, rationale_json,
              assumptions_json, warnings_json, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?::JSON,
              ?::JSON, ?::JSON, ?::JSON)
            """,
            [
                option.option_id,
                run.recommendation_run_id,
                option.rank,
                option.strategy_mode,
                option.chip_action,
                option.expected_gross_points,
                option.transfer_penalty_points,
                option.expected_net_points,
                option.budget_used_millions,
                option.budget_remaining_millions,
                option.expected_budget_delta_millions,
                option.risk_score,
                option.confidence,
                option.summary,
                dump_json(option.rationale),
                dump_json(option.assumptions),
                dump_json(option.warnings),
                dump_json(option.model_dump(by_alias=True, mode="json")),
            ],
        )
