from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from pathlib import Path

import httpx

from raceweek.connectors.base import ConnectorResult
from raceweek.connectors.openf1 import (
    OPENF1_LICENSE_NOTE,
    OPENF1_SYNC_PRESETS,
    OpenF1Connector,
    OpenF1SessionContext,
)
from raceweek.storage.jsonio import load_json_value
from raceweek.storage.repository import DuckDbRepository

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "packages" / "fixtures"
Handler = Callable[[httpx.Request], httpx.Response]


def test_openf1_fetches_session_context_with_provenance_metadata() -> None:
    fixture = load_fixture("openf1_session_demo.json")
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        key = request.url.path.rsplit("/", 1)[-1]
        return httpx.Response(200, json=fixture.get(key, []))

    result = asyncio.run(fetch_context(handler))

    assert result.status.source == "openf1"
    assert result.status.status == "ok"
    assert result.raw_snapshot_id.startswith("snapshot_openf1_")
    assert len(result.response_hash) == 64
    assert result.http_status == 200
    assert result.request_paths == [
        "/meetings?meeting_key=meeting_demo_01",
        "/sessions?meeting_key=meeting_demo_01",
        "/drivers?meeting_key=meeting_demo_01",
        "/session_result?meeting_key=meeting_demo_01",
        "/starting_grid?meeting_key=meeting_demo_01",
        "/race_control?meeting_key=meeting_demo_01",
        "/weather?meeting_key=meeting_demo_01",
    ]
    assert [call.url.path for call in calls] == [
        "/v1/meetings",
        "/v1/sessions",
        "/v1/drivers",
        "/v1/session_result",
        "/v1/starting_grid",
        "/v1/race_control",
        "/v1/weather",
    ]
    assert result.data.meetings[0].meeting_key == "meeting_demo_01"
    assert result.data.sessions[0].session_key == "session_demo_race"
    assert result.data.weather[0].track_temperature == 39
    assert result.data.race_control[0].message == "No penalties pending in demo snapshot."


def test_openf1_degrades_on_failed_fetch_without_exposing_request_secrets() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/sessions":
            return httpx.Response(503, json={"error": "upstream unavailable"})
        return httpx.Response(200, json=[])

    result = asyncio.run(fetch_context(handler))

    assert result.status.status == "degraded"
    assert result.status.severity == "warning"
    assert "OpenF1 request failed" in result.status.message
    assert result.http_status == 503
    assert result.data.meetings == []
    assert result.request_paths == [
        "/meetings?meeting_key=meeting_demo_01",
        "/sessions?meeting_key=meeting_demo_01",
    ]
    assert "token" not in result.status.message.lower()


def test_openf1_degrades_on_invalid_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not-json")

    result = asyncio.run(fetch_context(handler))

    assert result.status.status == "degraded"
    assert "valid JSON" in result.status.message
    assert result.http_status == 200


def test_openf1_connector_result_persists_source_snapshot(tmp_path: Path) -> None:
    fixture = load_fixture("openf1_session_demo.json")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=fixture.get(request.url.path.rsplit("/", 1)[-1], []))

    result = asyncio.run(fetch_context(handler))
    repository = DuckDbRepository(tmp_path / "raceweek.duckdb")

    repository.save_connector_result(
        result,
        request_url_template="https://api.openf1.org/v1/{endpoint}",
        license_note=OPENF1_LICENSE_NOTE,
        normalization_version="openf1-normalizer-v1",
    )

    with repository.connect() as connection:
        row = connection.execute(
            """
            SELECT source_name, request_method, request_params_json, raw_json,
                   content_hash, http_status, status, error_message
            FROM source_snapshots
            WHERE snapshot_id = ?
            """,
            [result.raw_snapshot_id],
        ).fetchone()
        status_row = connection.execute(
            "SELECT payload_json FROM data_source_statuses WHERE source = 'openf1'"
        ).fetchone()

    assert row is not None
    assert row[0] == "openf1"
    assert row[1] == "GET"
    assert load_json_value(row[2]) == {"requestPaths": result.request_paths}
    assert load_json_value(row[3])["meetings"][0]["meeting_key"] == "meeting_demo_01"
    assert row[4] == result.response_hash
    assert row[5] == 200
    assert row[6] == "ok"
    assert row[7] is None
    assert status_row is not None
    assert load_json_value(status_row[0])["status"] == "ok"


async def fetch_context(handler: Handler) -> ConnectorResult[OpenF1SessionContext]:
    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        connector = OpenF1Connector(
            base_url="https://api.openf1.test/v1",
            client=client,
        )
        return await connector.fetch_session_context("meeting_demo_01")


def test_openf1_sync_presets_control_endpoint_scope() -> None:
    assert OPENF1_SYNC_PRESETS["light"] == [
        "meetings",
        "sessions",
        "drivers",
        "session_result",
        "starting_grid",
        "race_control",
        "weather",
    ]
    assert len(OPENF1_SYNC_PRESETS["race_week"]) == 13
    assert "car_data" not in OPENF1_SYNC_PRESETS["race_week"]
    assert OPENF1_SYNC_PRESETS["telemetry"][-1] == "car_data"


def test_openf1_race_week_preset_fetches_required_context_without_car_data() -> None:
    fixture = load_fixture("openf1_session_demo.json")
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        endpoint = request.url.path.rsplit("/", 1)[-1]
        calls.append(endpoint)
        return httpx.Response(200, json=fixture.get(endpoint, []))

    transport = httpx.MockTransport(handler)

    async def run() -> ConnectorResult[OpenF1SessionContext]:
        async with httpx.AsyncClient(transport=transport) as client:
            connector = OpenF1Connector(
                base_url="https://api.openf1.test/v1",
                client=client,
            )
            return await connector.fetch_session_context("meeting_demo_01", preset="race_week")

    result = asyncio.run(run())

    assert result.status.status == "ok"
    assert calls == OPENF1_SYNC_PRESETS["race_week"]
    assert "car_data" not in calls


def load_fixture(name: str) -> dict[str, object]:
    with (FIXTURES / name).open() as file:
        payload: dict[str, object] = json.load(file)
    return payload
