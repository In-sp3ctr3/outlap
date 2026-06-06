from __future__ import annotations

from pathlib import Path
from threading import RLock
from typing import Any

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
    utc_now,
)
from raceweek.storage.fixtures import (
    DemoState,
    seed_demo_state,
)
from raceweek.storage.fixtures import (
    provider_configs as default_provider_configs,
)
from raceweek.storage.jsonio import dump_json, load_json_value
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

    def reset_real_data(self) -> DemoState:
        with self._lock:
            self.apply_migrations()
            state = seed_demo_state()
            with self.connect() as connection:
                clear_tables(connection)
                save_demo_source_snapshots(connection)
                save_data_sources(connection, state.data_sources.values())
                save_provider_configs(connection, default_provider_configs())
                save_json_setting(connection, "current_event_id", state.current_event_id)
                save_json_setting(connection, "data_mode", "real")
                save_json_setting(connection, "allow_demo_fallback", False)
                save_json_setting(connection, "first_run_completed", True)
            return state

    def load_state(self) -> DemoState:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                asset_count_row = connection.execute(
                    "SELECT count(*) FROM fantasy_assets"
                ).fetchone()
            asset_count = 0 if asset_count_row is None else int(asset_count_row[0])
            if asset_count == 0:
                return seed_demo_state()

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
                    return seed_demo_state()
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
                fallback = seed_demo_state()
                return DemoState(
                    assets=assets,
                    scores=[
                        FantasyAssetScore.model_validate(load_json_value(row[0]))
                        for row in connection.execute(
                            "SELECT payload_json FROM fantasy_asset_scores ORDER BY asset_id"
                        ).fetchall()
                    ],
                    team=FantasyTeamSnapshot.model_validate(load_json_value(team_row[0])),
                    current_event_id=str(
                        _load_json_setting_default(
                            connection,
                            "current_event_id",
                            fallback.current_event_id,
                        )
                    ),
                    race_data=_load_json_setting_default(
                        connection,
                        "race_data",
                        fallback.race_data,
                    ),
                    news=_load_json_setting_default(connection, "news", fallback.news),
                    league=_load_json_setting_default(connection, "league", fallback.league),
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

    def save_selected_team(self, team: FantasyTeamSnapshot) -> None:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                if team.slot is not None:
                    existing_rows = connection.execute(
                        "SELECT team_snapshot_id, payload_json FROM user_fantasy_teams"
                    ).fetchall()
                    for team_snapshot_id, payload_json in existing_rows:
                        payload = load_json_value(payload_json)
                        if isinstance(payload, dict) and payload.get("slot") == team.slot:
                            connection.execute(
                                "DELETE FROM chip_states WHERE team_snapshot_id = ?",
                                [team_snapshot_id],
                            )
                            connection.execute(
                                "DELETE FROM user_team_assets WHERE team_snapshot_id = ?",
                                [team_snapshot_id],
                            )
                            connection.execute(
                                "DELETE FROM user_fantasy_teams WHERE team_snapshot_id = ?",
                                [team_snapshot_id],
                            )
                _insert_team(connection, team)

    def save_current_teams(self, teams: list[FantasyTeamSnapshot]) -> None:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                connection.execute("DELETE FROM chip_states")
                connection.execute("DELETE FROM user_team_assets")
                connection.execute("DELETE FROM user_fantasy_teams")
                for team in teams:
                    _insert_team(connection, team)

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

    def save_public_form_features(
        self,
        event_id: str,
        scores: list[FantasyAssetScore],
        *,
        source_snapshot_id: str,
    ) -> None:
        with self._lock:
            self.apply_migrations()
            now = utc_now()
            with self.connect() as connection:
                for score in scores:
                    feature_id = f"form_{event_id}_{score.asset_id}_{source_snapshot_id}"
                    payload = {
                        "eventId": event_id,
                        "assetId": score.asset_id,
                        "featureKey": "public_form_points",
                        "featureValue": score.fantasy_points,
                        "sourceMode": "rules_engine_estimate",
                        "sourceSnapshotId": source_snapshot_id,
                        "calculatedAt": now.isoformat(),
                    }
                    connection.execute(
                        """
                        INSERT OR REPLACE INTO public_form_features (
                          feature_id, event_id, asset_id, feature_key, feature_value,
                          source_mode, source_snapshot_id, calculated_at, payload_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?::JSON)
                        """,
                        [
                            feature_id,
                            event_id,
                            score.asset_id,
                            "public_form_points",
                            score.fantasy_points,
                            "rules_engine_estimate",
                            source_snapshot_id,
                            now,
                            dump_json(payload),
                        ],
                    )

    def public_form_feature_count(self, event_id: str | None = None) -> int:
        query = "SELECT count(*) FROM public_form_features"
        params: list[object] = []
        if event_id:
            query += " WHERE event_id = ?"
            params.append(event_id)
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                row = connection.execute(query, params).fetchone()
        return 0 if row is None else int(row[0])

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

    def save_real_league(self, league: dict[str, object]) -> None:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                save_json_setting(connection, "real_league", league)

    def get_json_setting(self, key: str, default: Any = None) -> Any:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                row = connection.execute(
                    "SELECT setting_value_json FROM app_settings WHERE setting_key = ?",
                    [key],
                ).fetchone()
        return default if row is None else load_json_value(row[0])

    def set_json_setting(self, key: str, value: Any) -> None:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                save_json_setting(connection, key, value)

    def save_import_job(
        self,
        *,
        job_id: str,
        template_type: str,
        content_hash: str,
        status: str,
        row_count: int,
        summary: str,
        payload: dict[str, object],
    ) -> None:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                connection.execute(
                    "DELETE FROM import_jobs WHERE template_type = ? AND content_hash = ?",
                    [template_type, content_hash],
                )
                connection.execute(
                    """
                    INSERT INTO import_jobs (
                      job_id, template_type, source_mode, content_hash, status,
                      row_count, created_at, summary, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?::JSON)
                    """,
                    [
                        job_id,
                        template_type,
                        "manual",
                        content_hash,
                        status,
                        row_count,
                        utc_now(),
                        summary,
                        dump_json(payload),
                    ],
                )

    def real_assets(self) -> list[FantasyAsset]:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                rows = connection.execute(
                    """
                    SELECT payload_json
                    FROM fantasy_assets
                    WHERE coalesce(source_snapshot_id, '') NOT LIKE 'snapshot_demo%'
                    ORDER BY display_name
                    """
                ).fetchall()
        return [FantasyAsset.model_validate(load_json_value(row[0])) for row in rows]

    def real_scores(self, event_id: str | None = None) -> list[FantasyAssetScore]:
        query = """
            SELECT payload_json
            FROM fantasy_asset_scores
            WHERE coalesce(source_snapshot_id, '') NOT LIKE 'snapshot_demo%'
        """
        params: list[object] = []
        if event_id:
            query += " AND event_id = ?"
            params.append(event_id)
        query += " ORDER BY captured_at DESC, asset_id"
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                rows = connection.execute(query, params).fetchall()
        return [FantasyAssetScore.model_validate(load_json_value(row[0])) for row in rows]

    def real_teams(self, slot: int | None = None) -> list[FantasyTeamSnapshot]:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                rows = connection.execute(
                    """
                    SELECT payload_json
                    FROM user_fantasy_teams
                    WHERE coalesce(source_snapshot_id, '') NOT LIKE 'snapshot_demo%'
                    ORDER BY captured_at DESC
                    """
                ).fetchall()
        teams = [FantasyTeamSnapshot.model_validate(load_json_value(row[0])) for row in rows]
        teams = sorted(teams, key=lambda team: (team.slot or 99, team.team_snapshot_id))
        return [team for team in teams if team.slot == slot] if slot is not None else teams

    def real_league(self) -> dict[str, object] | None:
        value = self.get_json_setting("real_league")
        return value if isinstance(value, dict) else None

    def latest_snapshot_time(self, snapshot_prefix: str) -> Any:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                row = connection.execute(
                    """
                    SELECT max(fetched_at)
                    FROM source_snapshots
                    WHERE snapshot_id LIKE ?
                    """,
                    [f"{snapshot_prefix}%"],
                ).fetchone()
        return None if row is None else row[0]

    def save_race_context(self, openf1_result: Any, jolpica_result: Any) -> int:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                write_source_snapshot(
                    connection=connection,
                    snapshot_id=openf1_result.raw_snapshot_id,
                    source_name=openf1_result.source,
                    source_version="public-api",
                    connector_version=openf1_result.status.connector_version,
                    request_method="GET",
                    request_url_template="https://api.openf1.org/v1/{endpoint}",
                    request_params={"requestPaths": openf1_result.request_paths},
                    http_status=openf1_result.http_status,
                    payload=openf1_result.raw_payload,
                    license_note=openf1_result.status.license_note,
                    normalization_version="openf1-normalizer-v1",
                    status=openf1_result.status.status,
                    error_message=(
                        openf1_result.status.message
                        if openf1_result.status.status != "ok"
                        else None
                    ),
                )
                write_source_snapshot(
                    connection=connection,
                    snapshot_id=jolpica_result.raw_snapshot_id,
                    source_name=jolpica_result.source,
                    source_version="public-api",
                    connector_version=jolpica_result.status.connector_version,
                    request_method="GET",
                    request_url_template="https://api.jolpi.ca/ergast/f1/{path}.json",
                    request_params={"requestPaths": jolpica_result.request_paths},
                    http_status=jolpica_result.http_status,
                    payload=jolpica_result.raw_payload,
                    license_note=jolpica_result.status.license_note,
                    normalization_version="jolpica-normalizer-v1",
                    status=jolpica_result.status.status,
                    error_message=(
                        jolpica_result.status.message
                        if jolpica_result.status.status != "ok"
                        else None
                    ),
                )
                save_data_sources(connection, [openf1_result.status, jolpica_result.status])
                row_count = self._write_race_rows(connection, openf1_result, jolpica_result)
                self._write_sync_run(connection, openf1_result, "race_context", row_count)
                self._write_sync_run(connection, jolpica_result, "race_context", row_count)
        return row_count

    def race_meetings(self) -> list[dict[str, Any]]:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                rows = connection.execute(
                    """
                    SELECT payload_json
                    FROM race_context_meetings
                    ORDER BY updated_at DESC, meeting_key
                    """
                ).fetchall()
        return _dict_rows(rows)

    def race_sessions(self, meeting_key: str) -> list[dict[str, Any]]:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                rows = connection.execute(
                    """
                    SELECT payload_json
                    FROM race_context_sessions
                    WHERE meeting_key = ?
                    ORDER BY updated_at DESC, session_key
                    """,
                    [meeting_key],
                ).fetchall()
        return _dict_rows(rows)

    def race_domain_count(self, domain_key: str) -> int:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                if domain_key == "race.calendar":
                    row = connection.execute(
                        "SELECT count(*) FROM race_context_meetings"
                    ).fetchone()
                elif domain_key in {"race.current_meeting", "race.sessions"}:
                    table = (
                        "race_context_meetings"
                        if domain_key == "race.current_meeting"
                        else "race_context_sessions"
                    )
                    row = connection.execute(f"SELECT count(*) FROM {table}").fetchone()
                else:
                    row = connection.execute(
                        "SELECT count(*) FROM race_context_events WHERE domain_key = ?",
                        [domain_key],
                    ).fetchone()
        return 0 if row is None else int(row[0])

    def latest_race_context_time(self, domain_key: str) -> Any:
        with self._lock:
            self.apply_migrations()
            with self.connect() as connection:
                if domain_key in {"race.calendar", "race.current_meeting"}:
                    row = connection.execute(
                        "SELECT max(updated_at) FROM race_context_meetings"
                    ).fetchone()
                elif domain_key == "race.sessions":
                    row = connection.execute(
                        "SELECT max(updated_at) FROM race_context_sessions"
                    ).fetchone()
                else:
                    row = connection.execute(
                        "SELECT max(updated_at) FROM race_context_events WHERE domain_key = ?",
                        [domain_key],
                    ).fetchone()
        return None if row is None else row[0]

    def _write_race_rows(
        self,
        connection: duckdb.DuckDBPyConnection,
        openf1_result: Any,
        jolpica_result: Any,
    ) -> int:
        now = utc_now()
        row_count = 0
        for meeting in openf1_result.data.meetings:
            meeting_key = str(meeting.meeting_key)
            payload = {
                "meetingKey": meeting_key,
                "meetingName": meeting.meeting_name or f"Meeting {meeting_key}",
                "circuitName": meeting.circuit_short_name,
                "countryName": meeting.country_name,
                "location": meeting.location,
                "season": meeting.year,
                "startsAt": meeting.date_start.isoformat() if meeting.date_start else None,
                "endsAt": meeting.date_end.isoformat() if meeting.date_end else None,
                "sourceKey": openf1_result.source,
                "sourceSnapshotId": openf1_result.raw_snapshot_id,
            }
            connection.execute(
                """
                INSERT OR REPLACE INTO race_context_meetings (
                  meeting_key, season, round_number, meeting_name, source_key, source_mode,
                  source_snapshot_id, updated_at, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?::JSON)
                """,
                [
                    meeting_key,
                    meeting.year,
                    None,
                    meeting.meeting_name or f"Meeting {meeting_key}",
                    openf1_result.source,
                    "real",
                    openf1_result.raw_snapshot_id,
                    now,
                    dump_json(payload),
                ],
            )
            row_count += 1
        for race in jolpica_result.data.races:
            meeting_key = f"jolpica_{race.season}_{race.round_number}"
            payload = {
                "meetingKey": meeting_key,
                "meetingName": race.race_name,
                "circuitName": race.circuit_name,
                "countryName": None,
                "location": None,
                "season": race.season,
                "roundNumber": race.round_number,
                "startsAt": race.starts_at.isoformat() if race.starts_at else None,
                "sourceKey": jolpica_result.source,
                "sourceSnapshotId": jolpica_result.raw_snapshot_id,
            }
            connection.execute(
                """
                INSERT OR REPLACE INTO race_context_meetings (
                  meeting_key, season, round_number, meeting_name, source_key, source_mode,
                  source_snapshot_id, updated_at, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?::JSON)
                """,
                [
                    meeting_key,
                    race.season,
                    race.round_number,
                    race.race_name,
                    jolpica_result.source,
                    "real",
                    jolpica_result.raw_snapshot_id,
                    now,
                    dump_json(payload),
                ],
            )
            row_count += 1
        for session in openf1_result.data.sessions:
            payload = {
                "sessionKey": str(session.session_key),
                "meetingKey": str(session.meeting_key),
                "sessionName": session.session_name,
                "sessionType": session.session_type,
                "startsAt": session.date_start.isoformat() if session.date_start else None,
                "endsAt": session.date_end.isoformat() if session.date_end else None,
                "sourceKey": openf1_result.source,
                "sourceSnapshotId": openf1_result.raw_snapshot_id,
            }
            connection.execute(
                """
                INSERT OR REPLACE INTO race_context_sessions (
                  session_key, meeting_key, session_name, session_type, source_key,
                  source_mode, source_snapshot_id, updated_at, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?::JSON)
                """,
                [
                    str(session.session_key),
                    str(session.meeting_key),
                    session.session_name,
                    session.session_type,
                    openf1_result.source,
                    "real",
                    openf1_result.raw_snapshot_id,
                    now,
                    dump_json(payload),
                ],
            )
            row_count += 1
        for index, weather in enumerate(openf1_result.data.weather):
            payload = {
                "sessionKey": str(weather.session_key),
                "observedAt": weather.date.isoformat() if weather.date else None,
                "airTemperature": weather.air_temperature,
                "trackTemperature": weather.track_temperature,
                "rainfall": weather.rainfall,
                "windSpeed": weather.wind_speed,
                "sourceKey": openf1_result.source,
                "sourceSnapshotId": openf1_result.raw_snapshot_id,
            }
            self._write_race_event(
                connection,
                f"weather_{weather.session_key}_{index}",
                "race.weather",
                str(weather.session_key),
                openf1_result,
                payload,
                now,
            )
            row_count += 1
        for index, event in enumerate(openf1_result.data.race_control):
            payload = {
                "sessionKey": str(event.session_key) if event.session_key is not None else None,
                "category": event.category,
                "flag": event.flag,
                "message": event.message,
                "occurredAt": event.date.isoformat() if event.date else None,
                "sourceKey": openf1_result.source,
                "sourceSnapshotId": openf1_result.raw_snapshot_id,
            }
            self._write_race_event(
                connection,
                f"race_control_{event.session_key}_{index}",
                "race.race_control",
                str(event.session_key) if event.session_key is not None else None,
                openf1_result,
                payload,
                now,
            )
            row_count += 1
        return row_count

    def _write_race_event(
        self,
        connection: duckdb.DuckDBPyConnection,
        event_key: str,
        domain_key: str,
        session_key: str | None,
        result: Any,
        payload: dict[str, Any],
        updated_at: Any,
    ) -> None:
        connection.execute(
            """
            INSERT OR REPLACE INTO race_context_events (
              event_key, domain_key, meeting_key, session_key, source_key, source_mode,
              source_snapshot_id, updated_at, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?::JSON)
            """,
            [
                event_key,
                domain_key,
                None,
                session_key,
                result.source,
                "real",
                result.raw_snapshot_id,
                updated_at,
                dump_json(payload),
            ],
        )

    def _write_sync_run(
        self,
        connection: duckdb.DuckDBPyConnection,
        result: Any,
        domain: str,
        row_count: int,
    ) -> None:
        now = utc_now()
        connection.execute(
            """
            INSERT OR REPLACE INTO sync_runs (
              sync_run_id, source_key, source_domain, status, started_at, finished_at,
              request_path, response_hash, row_count, error_class, error_message, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?::JSON)
            """,
            [
                f"sync_{result.source}_{result.raw_snapshot_id}",
                result.source,
                domain,
                "success" if result.status.status == "ok" else "error",
                result.fetched_at,
                now,
                ";".join(result.request_paths),
                result.response_hash,
                row_count,
                None if result.status.status == "ok" else "ConnectorError",
                None if result.status.status == "ok" else result.status.message,
                dump_json(
                    {
                        "sourceSnapshotId": result.raw_snapshot_id,
                        "status": result.status.model_dump(by_alias=True, mode="json"),
                    }
                ),
            ],
        )

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


def _dict_rows(rows: list[tuple[Any, ...]]) -> list[dict[str, Any]]:
    values = [load_json_value(row[0]) for row in rows]
    return [value for value in values if isinstance(value, dict)]


def _load_json_setting_default(
    connection: duckdb.DuckDBPyConnection,
    key: str,
    default: Any,
) -> Any:
    row = connection.execute(
        "SELECT setting_value_json FROM app_settings WHERE setting_key = ?",
        [key],
    ).fetchone()
    return default if row is None else load_json_value(row[0])


def _insert_team(connection: duckdb.DuckDBPyConnection, team: FantasyTeamSnapshot) -> None:
    connection.execute(
        """
        INSERT OR REPLACE INTO user_fantasy_teams (
          team_snapshot_id, team_name, event_id, cost_cap_millions,
          budget_used_millions, budget_remaining_millions, free_transfers,
          transfer_penalty_points, captured_at, source_snapshot_id, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?::JSON)
        """,
        [
            team.team_snapshot_id,
            team.team_name,
            team.event_id,
            team.cost_cap_millions,
            team.budget_used_millions,
            team.budget_remaining_millions,
            team.free_transfers,
            team.transfer_penalty_points,
            team.captured_at,
            team.source_snapshot_id,
            dump_json(team.model_dump(by_alias=True, mode="json")),
        ],
    )
    for asset in team.assets:
        connection.execute(
            """
            INSERT OR REPLACE INTO user_team_assets (
              team_snapshot_id, asset_id, asset_type, boost_multiplier
            ) VALUES (?, ?, ?, ?)
            """,
            [team.team_snapshot_id, asset.asset_id, asset.asset_type, asset.boost_multiplier],
        )
    for chip in team.chips:
        connection.execute(
            """
            INSERT OR REPLACE INTO chip_states (
              chip_state_id, team_snapshot_id, chip_name, status,
              used_event_id, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?::JSON)
            """,
            [
                f"{team.team_snapshot_id}_{chip.chip_name}",
                team.team_snapshot_id,
                chip.chip_name,
                chip.status,
                chip.used_event_id,
                dump_json(chip.model_dump(by_alias=True, mode="json")),
            ],
        )
