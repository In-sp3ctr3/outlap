from __future__ import annotations

import hashlib
from collections.abc import Iterable
from typing import Any

import duckdb

from raceweek.core.models import (
    DataSourceStatus,
    FantasyAsset,
    FantasyTeamSnapshot,
    ProviderConfig,
    utc_now,
)
from raceweek.storage.fixtures import FIXTURES, load_fixture
from raceweek.storage.jsonio import dump_json, load_json_value


def clear_tables(connection: duckdb.DuckDBPyConnection) -> None:
    for table in [
        "recommendation_options",
        "recommendation_runs",
        "projections",
        "projection_runs",
        "chip_states",
        "user_team_assets",
        "user_fantasy_teams",
        "fantasy_assets",
        "provider_configs",
        "data_source_statuses",
        "source_snapshots",
        "app_settings",
    ]:
        connection.execute(f"DELETE FROM {table}")


def save_demo_source_snapshots(connection: duckdb.DuckDBPyConnection) -> None:
    fixture_map = {
        "snapshot_demo_market_01": ("manual_import", "fantasy_market_demo.json"),
        "snapshot_demo_team_01": ("manual_import", "fantasy_team_demo.json"),
        "snapshot_demo_race_01": ("openf1", "race_calendar_demo.json"),
        "snapshot_demo_news_01": ("news", "news_demo.json"),
        "snapshot_demo_league_01": ("manual_import", "league_demo.json"),
    }
    for snapshot_id, (source, fixture_name) in fixture_map.items():
        save_source_snapshot(
            connection=connection,
            snapshot_id=snapshot_id,
            source_name=source,
            connector_version=f"{source}-demo-v1",
            request_method="LOCAL",
            request_url_template=str(FIXTURES / fixture_name),
            payload=load_fixture(fixture_name),
            license_note="Synthetic fixture data",
        )


def save_source_snapshot(
    connection: duckdb.DuckDBPyConnection,
    snapshot_id: str,
    source_name: str,
    connector_version: str,
    request_method: str,
    request_url_template: str,
    payload: Any,
    license_note: str,
) -> None:
    raw = dump_json(payload)
    connection.execute("DELETE FROM source_snapshots WHERE snapshot_id = ?", [snapshot_id])
    connection.execute(
        """
        INSERT INTO source_snapshots (
          snapshot_id, source_name, source_version, connector_version,
          request_method, request_url_template, request_params_json,
          fetched_at, http_status, content_hash, raw_storage_path,
          raw_json, license_note, normalization_version, status, error_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?::JSON, ?, ?, ?, ?, ?::JSON, ?, ?, ?, ?)
        """,
        [
            snapshot_id,
            source_name,
            "demo-fixture",
            connector_version,
            request_method,
            request_url_template,
            "{}",
            utc_now(),
            200,
            hashlib.sha256(raw.encode()).hexdigest(),
            None,
            raw,
            license_note,
            "demo-normalizer-v1",
            "ok",
            None,
        ],
    )


def save_assets(
    connection: duckdb.DuckDBPyConnection,
    event_id: str,
    assets: list[FantasyAsset],
) -> None:
    connection.execute("DELETE FROM fantasy_assets")
    for asset in assets:
        connection.execute(
            """
            INSERT INTO fantasy_assets (
              asset_id, event_id, asset_type, display_name,
              price_millions, source_snapshot_id, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?::JSON)
            """,
            [
                asset.asset_id,
                event_id,
                asset.asset_type,
                asset.display_name,
                asset.price_millions,
                asset.source_snapshot_id,
                dump_json(asset.model_dump(by_alias=True, mode="json")),
            ],
        )


def save_team(connection: duckdb.DuckDBPyConnection, team: FantasyTeamSnapshot) -> None:
    connection.execute("DELETE FROM chip_states")
    connection.execute("DELETE FROM user_team_assets")
    connection.execute("DELETE FROM user_fantasy_teams")
    connection.execute(
        """
        INSERT INTO user_fantasy_teams (
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
            INSERT INTO user_team_assets (
              team_snapshot_id, asset_id, asset_type, boost_multiplier
            ) VALUES (?, ?, ?, ?)
            """,
            [team.team_snapshot_id, asset.asset_id, asset.asset_type, asset.boost_multiplier],
        )
    for chip in team.chips:
        connection.execute(
            """
            INSERT INTO chip_states (
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


def save_data_sources(
    connection: duckdb.DuckDBPyConnection,
    statuses: Iterable[DataSourceStatus],
) -> None:
    for source_status in statuses:
        connection.execute(
            "DELETE FROM data_source_statuses WHERE source = ?",
            [source_status.source],
        )
        connection.execute(
            """
            INSERT INTO data_source_statuses (
              source, status, severity, message, last_successful_sync_at,
              freshness, connector_version, license_note, action_required,
              payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?::JSON)
            """,
            [
                source_status.source,
                source_status.status,
                source_status.severity,
                source_status.message,
                source_status.last_successful_sync_at,
                source_status.freshness,
                source_status.connector_version,
                source_status.license_note,
                source_status.action_required,
                dump_json(source_status.model_dump(by_alias=True, mode="json")),
            ],
        )


def save_provider_configs(
    connection: duckdb.DuckDBPyConnection,
    configs: Iterable[ProviderConfig],
) -> None:
    for config in configs:
        connection.execute(
            "DELETE FROM provider_configs WHERE provider_name = ?",
            [config.provider_name],
        )
        connection.execute(
            """
            INSERT INTO provider_configs (
              provider_config_id, provider_name, display_name, default_model,
              enabled, supports_streaming, supports_tools, key_configured,
              payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?::JSON)
            """,
            [
                f"provider_{config.provider_name}",
                config.provider_name,
                config.display_name,
                config.default_model,
                config.enabled,
                config.supports_streaming,
                config.supports_tools,
                config.key_configured,
                dump_json(config.model_dump(by_alias=True, mode="json")),
            ],
        )


def save_json_setting(connection: duckdb.DuckDBPyConnection, key: str, value: Any) -> None:
    connection.execute("DELETE FROM app_settings WHERE setting_key = ?", [key])
    connection.execute(
        "INSERT INTO app_settings VALUES (?, ?::JSON, ?)",
        [key, dump_json(value), utc_now()],
    )


def load_json_setting(connection: duckdb.DuckDBPyConnection, key: str) -> Any:
    row = connection.execute(
        "SELECT setting_value_json FROM app_settings WHERE setting_key = ?",
        [key],
    ).fetchone()
    if row is None:
        raise RuntimeError(f"Missing app setting {key}")
    return load_json_value(row[0])
