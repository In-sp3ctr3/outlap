from __future__ import annotations

from pathlib import Path
from threading import RLock

import duckdb

from raceweek.connectors.base import ConnectorResult
from raceweek.core.models import (
    DataSourceStatus,
    FantasyAsset,
    FantasyAssetScore,
    FantasyTeamSnapshot,
    ProjectionRunResult,
    ProviderConfig,
    RecommendationRunResult,
)
from raceweek.storage.fixtures import (
    DemoState,
    seed_demo_state,
)
from raceweek.storage.fixtures import (
    provider_configs as default_provider_configs,
)
from raceweek.storage.jsonio import load_json_value
from raceweek.storage.runs import (
    load_projection_run,
    load_projection_runs,
    load_recommendation_run,
    load_recommendation_runs,
    save_projection_run,
    save_recommendation_run,
)
from raceweek.storage.seed import (
    clear_tables,
    load_json_setting,
    save_assets,
    save_data_sources,
    save_demo_source_snapshots,
    save_json_setting,
    save_provider_configs,
    save_scores,
    save_team,
)
from raceweek.storage.seed import save_source_snapshot as write_source_snapshot

MIGRATIONS = Path(__file__).resolve().parent / "migrations"


class DuckDbRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()

    def connect(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(str(self.database_path))

    def apply_migrations(self) -> None:
        with self._lock, self.connect() as connection:
            for migration in sorted(MIGRATIONS.glob("*.sql")):
                connection.execute(migration.read_text())

    def table_names(self) -> set[str]:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                rows = connection.execute("SHOW TABLES").fetchall()
        return {str(row[0]) for row in rows}

    def reset_demo(self) -> DemoState:
        with self._lock:
            self.apply_migrations()
            state = seed_demo_state()
            with self.connect() as connection:
                clear_tables(connection)
                save_demo_source_snapshots(connection)
                save_data_sources(connection, state.data_sources.values())
                save_provider_configs(connection, default_provider_configs())
                save_assets(connection, state.current_event_id, state.assets)
                save_scores(connection, state.current_event_id, state.scores)
                save_team(connection, state.team)
                save_json_setting(connection, "current_event_id", state.current_event_id)
                save_json_setting(connection, "race_data", state.race_data)
                save_json_setting(connection, "news", state.news)
                save_json_setting(connection, "league", state.league)
            return self.load_state()

    def load_state(self) -> DemoState:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                asset_count_row = connection.execute(
                    "SELECT count(*) FROM fantasy_assets"
                ).fetchone()
            asset_count = 0 if asset_count_row is None else int(asset_count_row[0])
            if asset_count == 0:
                return self.reset_demo()

            with self.connect() as connection:
                assets = [
                    FantasyAsset.model_validate(load_json_value(row[0]))
                    for row in connection.execute(
                        "SELECT payload_json FROM fantasy_assets ORDER BY asset_id"
                    ).fetchall()
                ]
                team_row = connection.execute(
                    "SELECT payload_json FROM user_fantasy_teams ORDER BY captured_at DESC LIMIT 1"
                ).fetchone()
                if team_row is None:
                    raise RuntimeError("Demo database is missing a fantasy team")
                data_sources = {
                    status.source: status
                    for status in (
                        DataSourceStatus.model_validate(
                            _normalize_data_source_status(load_json_value(row[0]))
                        )
                        for row in connection.execute(
                            "SELECT payload_json FROM data_source_statuses ORDER BY source"
                        ).fetchall()
                    )
                }
                source_snapshot_ids = {
                    str(row[0])
                    for row in connection.execute(
                        "SELECT snapshot_id FROM source_snapshots ORDER BY snapshot_id"
                    ).fetchall()
                }
                return DemoState(
                    assets=assets,
                    scores=[
                        FantasyAssetScore.model_validate(load_json_value(row[0]))
                        for row in connection.execute(
                            "SELECT payload_json FROM fantasy_asset_scores ORDER BY asset_id"
                        ).fetchall()
                    ],
                    team=FantasyTeamSnapshot.model_validate(load_json_value(team_row[0])),
                    current_event_id=str(load_json_setting(connection, "current_event_id")),
                    race_data=load_json_setting(connection, "race_data"),
                    news=load_json_setting(connection, "news"),
                    league=load_json_setting(connection, "league"),
                    data_sources=data_sources,
                    source_snapshot_ids=source_snapshot_ids,
                    projection_runs=load_projection_runs(connection),
                    recommendation_runs=load_recommendation_runs(connection),
                )

    def save_team(self, team: FantasyTeamSnapshot) -> None:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                save_team(connection, team)

    def save_assets(self, event_id: str, assets: list[FantasyAsset]) -> None:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                save_assets(connection, event_id, assets)
                save_json_setting(connection, "current_event_id", event_id)

    def save_scores(self, event_id: str, scores: list[FantasyAssetScore]) -> None:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                save_scores(connection, event_id, scores)

    def save_data_source_status(self, status: DataSourceStatus) -> None:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                save_data_sources(connection, [status])

    def save_league(self, league: dict[str, object]) -> None:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                save_json_setting(connection, "league", league)

    def save_source_snapshot(
        self,
        snapshot_id: str,
        payload: dict[str, object],
        *,
        source_name: str = "manual_import",
        connector_version: str = "manual-import-v1",
        request_url_template: str = "manual://import",
    ) -> None:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                write_source_snapshot(
                    connection=connection,
                    snapshot_id=snapshot_id,
                    source_name=source_name,
                    connector_version=connector_version,
                    request_method="MANUAL",
                    request_url_template=request_url_template,
                    payload=payload,
                    license_note="User-provided local manual import",
                )

    def save_connector_result(
        self,
        result: ConnectorResult[object],
        *,
        request_url_template: str,
        license_note: str,
        source_version: str = "public-api",
        normalization_version: str = "connector-normalizer-v1",
    ) -> None:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                write_source_snapshot(
                    connection=connection,
                    snapshot_id=result.raw_snapshot_id,
                    source_name=result.source,
                    source_version=source_version,
                    connector_version=result.status.connector_version,
                    request_method="GET",
                    request_url_template=request_url_template,
                    request_params={"requestPaths": result.request_paths},
                    http_status=result.http_status,
                    payload=result.raw_payload,
                    license_note=license_note,
                    normalization_version=normalization_version,
                    status=result.status.status,
                    error_message=(
                        result.status.message if result.status.status != "ok" else None
                    ),
                )
                save_data_sources(connection, [result.status])

    def load_provider_configs(self) -> list[ProviderConfig]:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                rows = connection.execute(
                    "SELECT payload_json FROM provider_configs ORDER BY provider_name"
                ).fetchall()
                if not rows:
                    configs = default_provider_configs()
                    save_provider_configs(connection, configs)
                    return configs
        return [ProviderConfig.model_validate(load_json_value(row[0])) for row in rows]

    def save_projection_run(self, run: ProjectionRunResult) -> None:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                save_projection_run(connection, run)

    def get_projection_run(self, projection_run_id: str) -> ProjectionRunResult:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                return load_projection_run(connection, projection_run_id)

    def save_recommendation_run(self, run: RecommendationRunResult) -> None:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                save_recommendation_run(connection, run)

    def get_recommendation_run(self, recommendation_run_id: str) -> RecommendationRunResult:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                return load_recommendation_run(connection, recommendation_run_id)


def _normalize_data_source_status(payload: object) -> object:
    if isinstance(payload, dict) and payload.get("status") == "healthy":
        return {**payload, "status": "ok"}
    return payload
