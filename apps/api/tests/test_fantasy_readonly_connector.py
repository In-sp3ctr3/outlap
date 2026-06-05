from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path

import httpx

from raceweek.connectors.base import ConnectorResult
from raceweek.connectors.fantasy_readonly import (
    FANTASY_LICENSE_NOTE,
    FantasyReadOnlyConnector,
    FantasyReadOnlySnapshot,
)
from raceweek.storage.jsonio import load_json_value
from raceweek.storage.repository import DuckDbRepository

Handler = Callable[[httpx.Request], httpx.Response]


def test_fantasy_readonly_connector_uses_documented_get_paths_and_redacts_token() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path.endswith("/players"):
            return httpx.Response(
                200,
                json={"players": [{"id": "driver_1", "display_name": "Driver One"}]},
            )
        if request.url.path.endswith("/teams"):
            return httpx.Response(
                200,
                json={"teams": [{"id": "team_1", "name": "Constructor One"}]},
            )
        if request.url.path.endswith("/live_stats"):
            return httpx.Response(
                200,
                json={"live_stats": [{"player_id": "driver_1", "points": 12}]},
            )
        if request.url.path.endswith("/leaderboards/leagues"):
            return httpx.Response(200, json={"leaderboards": [{"rank": 1, "team_name": "Demo"}]})
        if request.url.path.endswith("/picked_teams/for_slot"):
            return httpx.Response(200, json={"picked_teams": [{"asset_ids": ["driver_1"]}]})
        return httpx.Response(404, json={})

    result = asyncio.run(fetch_snapshot(handler))

    assert result.status.source == "fantasy_readonly"
    assert result.status.status == "ok"
    assert isinstance(result.data, FantasyReadOnlySnapshot)
    assert result.data.players == [{"id": "driver_1", "display_name": "Driver One"}]
    assert result.data.teams == [{"id": "team_1", "name": "Constructor One"}]
    assert result.request_paths == [
        "/2022/players",
        "/2022/teams",
        "/2022/live_stats?game_period_id=gp_1",
        "/2022/leaderboards/leagues?league_id=league_1",
        "/2022/picked_teams/for_slot?game_period_id=gp_1&slot=1&user_global_id=user_1",
    ]
    assert all(call.method == "GET" for call in calls)
    assert all(call.headers["authorization"] == "Bearer secret-token" for call in calls)
    assert "secret-token" not in str(result.raw_payload)
    assert "secret-token" not in " ".join(result.request_paths)
    assert "secret-token" not in result.status.message


def test_fantasy_readonly_connector_degrades_without_exposing_token() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/teams"):
            return httpx.Response(503, json={"error": "unavailable"})
        return httpx.Response(200, json={"players": []})

    result = asyncio.run(fetch_snapshot(handler))

    assert result.status.status == "degraded"
    assert "Fantasy read-only request failed" in result.status.message
    assert "secret-token" not in result.status.message
    assert result.request_paths == ["/2022/players", "/2022/teams"]
    assert result.http_status == 503


def test_fantasy_readonly_connector_result_persists_without_token(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/players"):
            return httpx.Response(200, json={"players": []})
        if request.url.path.endswith("/teams"):
            return httpx.Response(200, json={"teams": []})
        if request.url.path.endswith("/live_stats"):
            return httpx.Response(200, json={"live_stats": []})
        if request.url.path.endswith("/leaderboards/leagues"):
            return httpx.Response(200, json={"leaderboards": []})
        return httpx.Response(200, json={"picked_teams": []})

    result = asyncio.run(fetch_snapshot(handler))
    repository = DuckDbRepository(tmp_path / "raceweek.duckdb")
    repository.save_connector_result(
        result,
        request_url_template="https://fantasy-api.formula1.com/partner_games/f1/{path}",
        license_note=FANTASY_LICENSE_NOTE,
        normalization_version="fantasy-readonly-normalizer-v1",
    )

    with repository.connect() as connection:
        row = connection.execute(
            "SELECT raw_json, request_params_json FROM source_snapshots WHERE snapshot_id = ?",
            [result.raw_snapshot_id],
        ).fetchone()

    assert row is not None
    assert "secret-token" not in str(load_json_value(row[0]))
    assert "secret-token" not in str(load_json_value(row[1]))


def test_fantasy_readonly_connector_has_no_mutation_methods() -> None:
    connector = FantasyReadOnlyConnector(
        base_url="https://fantasy-api.test/partner_games/f1",
        game_version="2022",
        session_token="secret-token",
    )

    assert not hasattr(connector, "submit_transfers")
    assert not hasattr(connector, "save_team")


async def fetch_snapshot(handler: Handler) -> ConnectorResult[FantasyReadOnlySnapshot]:
    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        connector = FantasyReadOnlyConnector(
            base_url="https://fantasy-api.test/partner_games/f1",
            game_version="2022",
            session_token="secret-token",
            client=client,
        )
        return await connector.fetch_game_snapshot(
            game_period_id="gp_1",
            league_id="league_1",
            slot=1,
            user_global_id="user_1",
        )
