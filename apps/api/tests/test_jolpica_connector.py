from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from pathlib import Path

import httpx

from raceweek.connectors.base import ConnectorResult
from raceweek.connectors.jolpica import JOLPICA_LICENSE_NOTE, JolpicaConnector
from raceweek.connectors.jolpica_normalize import JolpicaSeasonContext
from raceweek.storage.jsonio import load_json_value
from raceweek.storage.repository import DuckDbRepository

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "packages" / "fixtures"
Handler = Callable[[httpx.Request], httpx.Response]
FIXTURE_KEYS = {
    "2026": "calendar",
    "driverstandings": "driverStandings",
    "constructorstandings": "constructorStandings",
}


def test_jolpica_fetches_season_context_with_documented_paths() -> None:
    fixture = load_fixture("jolpica_season_demo.json")
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        key = request.url.path.rsplit("/", 1)[-1].replace(".json", "")
        if key in {"status", "pitstops", "laps"}:
            return httpx.Response(200, json=empty_mrdata_payload(key))
        return httpx.Response(200, json=fixture[FIXTURE_KEYS.get(key, key)])

    result = asyncio.run(fetch_context(handler))

    assert result.status.source == "jolpica"
    assert result.status.status == "ok"
    assert result.raw_snapshot_id.startswith("snapshot_jolpica_2026_")
    assert len(result.response_hash) == 64
    assert result.request_paths[:7] == [
        "/2026.json?limit=100&offset=0",
        "/2026/results.json?limit=100&offset=0",
        "/2026/qualifying.json?limit=100&offset=0",
        "/2026/sprint.json?limit=100&offset=0",
        "/2026/driverstandings.json?limit=100&offset=0",
        "/2026/constructorstandings.json?limit=100&offset=0",
        "/status.json?limit=100&offset=0",
    ]
    assert "/2026/1/pitstops.json?limit=100&offset=0" in result.request_paths
    assert "/2026/1/laps.json?limit=100&offset=0" in result.request_paths
    assert "/2026/1/status.json?limit=100&offset=0" in result.request_paths
    assert {call.url.path for call in calls} >= {
        "/ergast/f1/2026.json",
        "/ergast/f1/2026/results.json",
        "/ergast/f1/2026/qualifying.json",
        "/ergast/f1/2026/sprint.json",
        "/ergast/f1/2026/driverstandings.json",
        "/ergast/f1/2026/constructorstandings.json",
        "/ergast/f1/status.json",
        "/ergast/f1/2026/1/pitstops.json",
        "/ergast/f1/2026/1/laps.json",
        "/ergast/f1/2026/1/status.json",
    }
    assert result.data.races[0].race_name == "Harbor Night Grand Prix"
    assert result.data.race_results[0].driver_id == "driver_alpha"
    assert result.data.qualifying_results[0].position == 1
    assert result.data.driver_standings[0].points == 25
    assert result.data.constructor_standings[0].constructor_id == "constructor_one"


def test_jolpica_degrades_on_invalid_upstream_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/results.json"):
            return httpx.Response(502, json={"error": "bad gateway"})
        return httpx.Response(200, json={"MRData": {"RaceTable": {"Races": []}}})

    result = asyncio.run(fetch_context(handler))

    assert result.status.status == "degraded"
    assert result.status.severity == "warning"
    assert "Jolpica request failed" in result.status.message
    assert result.http_status == 502
    assert result.data.races == []
    assert result.request_paths == [
        "/2026.json?limit=100&offset=0",
        "/2026/results.json?limit=100&offset=0",
    ]


def test_jolpica_paginated_fetches_all_offsets() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        offset = int(request.url.params.get("offset", "0"))
        rows = [{"season": "2026", "round": str((offset // 100) + 1), "raceName": f"Race {offset}"}]
        return httpx.Response(
            200,
            json={
                "MRData": {
                    "limit": "100",
                    "offset": str(offset),
                    "total": "240",
                    "RaceTable": {"Races": rows},
                }
            },
        )

    transport = httpx.MockTransport(handler)

    async def run() -> tuple[dict[str, object], list[str]]:
        async with httpx.AsyncClient(transport=transport) as client:
            connector = JolpicaConnector(
                base_url="https://api.jolpi.test/ergast/f1",
                client=client,
            )
            payload, _status, request_paths = await connector._get_paginated("2026/results.json")
            return payload, request_paths

    payload, request_paths = asyncio.run(run())

    assert [call.url.params["offset"] for call in calls] == ["0", "100", "200"]
    assert request_paths == [
        "/2026/results.json?limit=100&offset=0",
        "/2026/results.json?limit=100&offset=100",
        "/2026/results.json?limit=100&offset=200",
    ]
    assert len(payload["MRData"]["RaceTable"]["Races"]) == 3


def test_jolpica_connector_result_persists_source_snapshot(tmp_path: Path) -> None:
    fixture = load_fixture("jolpica_season_demo.json")

    def handler(request: httpx.Request) -> httpx.Response:
        key = request.url.path.rsplit("/", 1)[-1].replace(".json", "")
        if key in {"status", "pitstops", "laps"}:
            return httpx.Response(200, json=empty_mrdata_payload(key))
        return httpx.Response(200, json=fixture[FIXTURE_KEYS.get(key, key)])

    result = asyncio.run(fetch_context(handler))
    repository = DuckDbRepository(tmp_path / "raceweek.duckdb")

    repository.save_connector_result(
        result,
        request_url_template="https://api.jolpi.ca/ergast/f1/{path}.json",
        license_note=JOLPICA_LICENSE_NOTE,
        normalization_version="jolpica-normalizer-v1",
    )

    with repository.connect() as connection:
        row = connection.execute(
            """
            SELECT source_name, request_params_json, content_hash, http_status, status
            FROM source_snapshots
            WHERE snapshot_id = ?
            """,
            [result.raw_snapshot_id],
        ).fetchone()

    assert row is not None
    assert row[0] == "jolpica"
    assert load_json_value(row[1]) == {"requestPaths": result.request_paths}
    assert row[2] == result.response_hash
    assert row[3] == 200
    assert row[4] == "ok"


async def fetch_context(handler: Handler) -> ConnectorResult[JolpicaSeasonContext]:
    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        connector = JolpicaConnector(
            base_url="https://api.jolpi.test/ergast/f1",
            client=client,
        )
        return await connector.fetch_season_context(2026)


def load_fixture(name: str) -> dict[str, object]:
    with (FIXTURES / name).open() as file:
        payload: dict[str, object] = json.load(file)
    return payload


def empty_mrdata_payload(key: str) -> dict[str, object]:
    table_key, list_key = {
        "status": ("StatusTable", "Status"),
        "pitstops": ("RaceTable", "Races"),
        "laps": ("RaceTable", "Races"),
    }[key]
    return {"MRData": {"limit": "100", "offset": "0", "total": "0", table_key: {list_key: []}}}
