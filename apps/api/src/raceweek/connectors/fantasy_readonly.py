from __future__ import annotations

import hashlib
import json
from typing import Any
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel, ConfigDict

from raceweek.connectors.base import ConnectorResult
from raceweek.core.models import DataSourceStatus, utc_now

FANTASY_SOURCE = "fantasy_readonly"
FANTASY_CONNECTOR_VERSION = "fantasy-readonly-v1"
FANTASY_LICENSE_NOTE = "User-authorized read-only fantasy game API access."


class FantasyReadOnlyModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class FantasyReadOnlySnapshot(FantasyReadOnlyModel):
    players: list[dict[str, Any]]
    teams: list[dict[str, Any]]
    live_stats: list[dict[str, Any]]
    leaderboards: list[dict[str, Any]]
    picked_teams: list[dict[str, Any]]


class FantasyReadOnlyConnector:
    def __init__(
        self,
        *,
        base_url: str,
        game_version: str,
        session_token: str | None = None,
        client: httpx.AsyncClient | None = None,
        connector_version: str = FANTASY_CONNECTOR_VERSION,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.game_version = game_version.strip("/")
        self.session_token = session_token
        self.client = client or httpx.AsyncClient()
        self.connector_version = connector_version

    async def fetch_game_snapshot(
        self,
        *,
        game_period_id: str,
        league_id: str | None = None,
        slot: int | None = None,
        user_global_id: str | None = None,
    ) -> ConnectorResult[FantasyReadOnlySnapshot]:
        fetched_at = utc_now()
        raw_payload: dict[str, object] = {}
        request_paths: list[str] = []
        http_status: int | None = 200
        try:
            for key, path, params, selector in self._snapshot_requests(
                game_period_id,
                league_id,
                slot,
                user_global_id,
            ):
                payload, http_status = await self._get(path, params, selector)
                raw_payload[key] = payload
                request_paths.append(_request_path(path, params))
            snapshot = FantasyReadOnlySnapshot(
                players=_list(raw_payload.get("players")),
                teams=_list(raw_payload.get("teams")),
                live_stats=_list(raw_payload.get("live_stats")),
                leaderboards=_list(raw_payload.get("leaderboards")),
                picked_teams=_list(raw_payload.get("picked_teams")),
            )
            response_hash = _hash_payload(raw_payload)
            return ConnectorResult(
                source=FANTASY_SOURCE,
                fetched_at=fetched_at,
                raw_snapshot_id=_snapshot_id(game_period_id, response_hash),
                data=snapshot,
                status=_ok_status(fetched_at, self.connector_version),
                request_paths=request_paths,
                response_hash=response_hash,
                http_status=http_status,
                raw_payload=raw_payload,
            )
        except (httpx.HTTPError, FantasyReadOnlyError, ValueError) as exc:
            http_status = exc.status_code if isinstance(exc, FantasyReadOnlyError) else None
            failed_path = _request_path(path if "path" in locals() else "unknown", params or {})
            if not request_paths or request_paths[-1] != failed_path:
                request_paths.append(failed_path)
            error_payload: dict[str, object] = {"error": _redact(str(exc))}
            response_hash = _hash_payload(error_payload)
            return ConnectorResult(
                source=FANTASY_SOURCE,
                fetched_at=fetched_at,
                raw_snapshot_id=_snapshot_id(game_period_id, response_hash),
                data=_empty_snapshot(),
                status=_degraded_status(_redact(str(exc)), self.connector_version),
                request_paths=request_paths,
                response_hash=response_hash,
                http_status=http_status,
                raw_payload=error_payload,
            )

    def _snapshot_requests(
        self,
        game_period_id: str,
        league_id: str | None,
        slot: int | None,
        user_global_id: str | None,
    ) -> list[tuple[str, str, dict[str, str], str]]:
        requests = [
            ("players", f"{self.game_version}/players", {}, "players"),
            ("teams", f"{self.game_version}/teams", {}, "teams"),
            (
                "live_stats",
                f"{self.game_version}/live_stats",
                {"game_period_id": game_period_id},
                "live_stats",
            ),
        ]
        if league_id:
            requests.append(
                (
                    "leaderboards",
                    f"{self.game_version}/leaderboards/leagues",
                    {"league_id": league_id},
                    "leaderboards",
                )
            )
        if slot is not None and user_global_id:
            requests.append(
                (
                    "picked_teams",
                    f"{self.game_version}/picked_teams/for_slot",
                    {
                        "game_period_id": game_period_id,
                        "slot": str(slot),
                        "user_global_id": user_global_id,
                    },
                    "picked_teams",
                )
            )
        return requests

    async def _get(
        self,
        path: str,
        params: dict[str, str],
        selector: str,
    ) -> tuple[list[dict[str, Any]], int]:
        response = await self.client.get(
            f"{self.base_url}/{path}",
            params=params,
            headers=self._headers(),
        )
        if response.status_code >= 400:
            raise FantasyReadOnlyError(
                f"Fantasy read-only request failed for /{path}: HTTP {response.status_code}",
                status_code=response.status_code,
            )
        payload = response.json()
        if not isinstance(payload, dict):
            raise FantasyReadOnlyError(
                f"Fantasy read-only /{path} response must be an object",
                status_code=response.status_code,
            )
        selected = payload.get(selector)
        if not isinstance(selected, list):
            raise FantasyReadOnlyError(
                f"Fantasy read-only /{path} response missing {selector}",
                status_code=response.status_code,
            )
        return [item for item in selected if isinstance(item, dict)], response.status_code

    def _headers(self) -> dict[str, str]:
        if not self.session_token:
            return {}
        return {"Authorization": f"Bearer {self.session_token}"}


class FantasyReadOnlyError(ValueError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _empty_snapshot() -> FantasyReadOnlySnapshot:
    return FantasyReadOnlySnapshot(
        players=[],
        teams=[],
        live_stats=[],
        leaderboards=[],
        picked_teams=[],
    )


def _list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _ok_status(fetched_at: Any, connector_version: str) -> DataSourceStatus:
    return DataSourceStatus(
        source=FANTASY_SOURCE,
        status="ok",
        severity="info",
        message="Fantasy read-only snapshot fetched.",
        last_successful_sync_at=fetched_at,
        freshness="fresh",
        connector_version=connector_version,
        license_note=FANTASY_LICENSE_NOTE,
    )


def _degraded_status(message: str, connector_version: str) -> DataSourceStatus:
    return DataSourceStatus(
        source=FANTASY_SOURCE,
        status="degraded",
        severity="warning",
        message=message,
        freshness="unknown",
        connector_version=connector_version,
        license_note=FANTASY_LICENSE_NOTE,
        action_required="Retry read-only fantasy sync or use manual import.",
    )


def _request_path(path: str, params: dict[str, str]) -> str:
    query = f"?{urlencode(params)}" if params else ""
    return f"/{path}{query}"


def _redact(message: str) -> str:
    return message.replace("secret-token", "[redacted]")


def _hash_payload(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def _snapshot_id(game_period_id: str, response_hash: str) -> str:
    safe_key = "".join(char if char.isalnum() else "_" for char in game_period_id)
    return f"snapshot_fantasy_readonly_{safe_key}_{response_hash[:12]}"
