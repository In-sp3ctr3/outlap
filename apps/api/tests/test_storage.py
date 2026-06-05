from pathlib import Path

from raceweek.core.optimizer import optimize_recommendations
from raceweek.core.projections import run_projection
from raceweek.storage.jsonio import dump_json, load_json_value
from raceweek.storage.repository import DuckDbRepository


def test_migrations_create_core_tables(tmp_path: Path) -> None:
    repository = DuckDbRepository(tmp_path / "raceweek.duckdb")
    repository.apply_migrations()

    tables = repository.table_names()

    assert {
        "source_snapshots",
        "fantasy_assets",
        "user_fantasy_teams",
        "user_team_assets",
        "chip_states",
        "projection_runs",
        "projections",
        "recommendation_runs",
        "recommendation_options",
        "provider_configs",
        "data_source_statuses",
        "app_settings",
    } <= tables


def test_seed_demo_persists_state_and_source_snapshots(tmp_path: Path) -> None:
    db_path = tmp_path / "raceweek.duckdb"
    repository = DuckDbRepository(db_path)
    repository.reset_demo()

    reloaded = DuckDbRepository(db_path).load_state()

    assert reloaded.current_event_id == "event_demo_01"
    assert len(reloaded.assets) >= 14
    assert reloaded.team.team_snapshot_id == "team_demo_01"
    assert reloaded.data_sources["manual_import"].status == "ok"
    assert reloaded.source_snapshot_ids == {
        "snapshot_demo_market_01",
        "snapshot_demo_team_01",
        "snapshot_demo_race_01",
        "snapshot_demo_news_01",
        "snapshot_demo_league_01",
    }


def test_load_state_normalizes_legacy_healthy_status(tmp_path: Path) -> None:
    db_path = tmp_path / "raceweek.duckdb"
    repository = DuckDbRepository(db_path)
    repository.reset_demo()
    with repository.connect() as connection:
        payload_row = connection.execute(
            "SELECT payload_json FROM data_source_statuses WHERE source = 'manual_import'"
        ).fetchone()
        assert payload_row is not None
        payload = load_json_value(payload_row[0])
        assert isinstance(payload, dict)
        payload["status"] = "healthy"
        connection.execute(
            "UPDATE data_source_statuses SET payload_json = ?::JSON WHERE source = 'manual_import'",
            [dump_json(payload)],
        )

    reloaded = DuckDbRepository(db_path).load_state()

    assert reloaded.data_sources["manual_import"].status == "ok"


def test_projection_and_recommendation_runs_persist(tmp_path: Path) -> None:
    db_path = tmp_path / "raceweek.duckdb"
    repository = DuckDbRepository(db_path)
    repository.reset_demo()
    state = repository.load_state()

    projection_run = run_projection(state.assets, event_id=state.current_event_id)
    repository.save_projection_run(projection_run)
    recommendation_run = optimize_recommendations(
        team=state.team,
        assets=state.assets,
        projections=projection_run.projections,
        event_id=state.current_event_id,
        strategy_mode="balanced",
        locked_asset_ids=[],
        banned_asset_ids=[],
        allowed_chips=[],
        max_options=3,
        projection_run_id=projection_run.projection_run_id,
        source_snapshot_ids=projection_run.source_snapshot_ids,
    )
    repository.save_recommendation_run(recommendation_run)

    reloaded = DuckDbRepository(db_path)

    assert reloaded.get_projection_run(projection_run.projection_run_id).projection_run_id
    assert reloaded.get_recommendation_run(
        recommendation_run.recommendation_run_id
    ).options[0].source_snapshot_ids
