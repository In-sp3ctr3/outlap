from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

import httpx

from raceweek.connectors.base import ConnectorResult
from raceweek.connectors.jolpica_normalize import (
    JolpicaSeasonContext,
    empty_context,
    normalize_context,
)
from raceweek.core.models import DataSourceStatus, utc_now

JOLPICA_SOURCE = "jolpica"
JOLPICA_CONNECTOR_VERSION = "jolpica-v1"
JOLPICA_LICENSE_NOTE = "Jolpica-F1 Ergast-compatible public API."


class JolpicaConnector:
    def __init__(
        self,
        *,
        base_url: str = "https://api.jolpi.ca/ergast/f1",
        client: httpx.AsyncClient | None = None,
        connector_version: str = JOLPICA_CONNECTOR_VERSION,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.AsyncClient()
        self.connector_version = connector_version

    async def fetch_season_context(self, season: int) -> ConnectorResult[JolpicaSeasonContext]:
        fetched_at = utc_now()
        raw_payload: dict[str, object] = {}
        request_paths: list[str] = []
        http_status: int | None = 200
        try:
            calendar, http_status, paths = await self._get_paginated(f"{season}.json")
            raw_payload["calendar"] = calendar
            request_paths.extend(paths)
            for key, path in _season_endpoint_paths(season).items():
                payload, http_status, paths = await self._get_paginated(path)
                raw_payload[key] = payload
                request_paths.extend(paths)
            for round_number in _calendar_rounds(calendar):
                for key, path in _round_endpoint_paths(season, round_number).items():
                    payload, http_status, paths = await self._get_paginated(path)
                    raw_payload[f"{key}:{round_number}"] = payload
                    request_paths.extend(paths)
            response_hash = _hash_payload(raw_payload)
            return ConnectorResult(
                source=JOLPICA_SOURCE,
                fetched_at=fetched_at,
                raw_snapshot_id=_snapshot_id(season, response_hash),
                data=normalize_context(raw_payload),
                status=_ok_status(fetched_at, self.connector_version),
                request_paths=request_paths,
                response_hash=response_hash,
                http_status=http_status,
                raw_payload=raw_payload,
            )
        except (httpx.HTTPError, JolpicaConnectorError, ValueError) as exc:
            http_status = exc.status_code if isinstance(exc, JolpicaConnectorError) else None
            failed_path = _request_path(path if "path" in locals() else f"{season}.json")
            if not request_paths or request_paths[-1] != failed_path:
                request_paths.append(failed_path)
            raw_payload = raw_payload or {"error": str(exc)}
            response_hash = _hash_payload(raw_payload)
            return ConnectorResult(
                source=JOLPICA_SOURCE,
                fetched_at=fetched_at,
                raw_snapshot_id=_snapshot_id(season, response_hash),
                data=empty_context(),
                status=_degraded_status(str(exc), self.connector_version),
                request_paths=request_paths,
                response_hash=response_hash,
                http_status=http_status,
                raw_payload=raw_payload,
            )

    async def _get(self, path: str) -> tuple[dict[str, Any], int]:
        payload, status_code = await self._get_page(path, limit=100, offset=0)
        return payload, status_code

    async def _get_paginated(self, path: str) -> tuple[dict[str, Any], int, list[str]]:
        limit = 100
        offset = 0
        pages: list[dict[str, Any]] = []
        request_paths: list[str] = []
        http_status = 200
        while True:
            payload, http_status = await self._get_page(path, limit=limit, offset=offset)
            pages.append(payload)
            request_paths.append(_request_path(path, limit=limit, offset=offset))
            total = _mrdata_int(payload, "total")
            offset += limit
            if offset >= total:
                break
        return _merge_pages(pages), http_status, request_paths

    async def _get_page(self, path: str, *, limit: int, offset: int) -> tuple[dict[str, Any], int]:
        response = await self.client.get(
            f"{self.base_url}/{path}",
            params={"limit": str(limit), "offset": str(offset)},
        )
        if response.status_code >= 400:
            raise JolpicaConnectorError(
                f"Jolpica request failed for /{path}: HTTP {response.status_code}",
                status_code=response.status_code,
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise JolpicaConnectorError(
                f"Jolpica /{path} response must be valid JSON",
                status_code=response.status_code,
            ) from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("MRData"), dict):
            raise JolpicaConnectorError(
                f"Jolpica /{path} response must contain MRData",
                status_code=response.status_code,
            )
        return payload, response.status_code


class JolpicaConnectorError(ValueError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _season_endpoint_paths(season: int) -> dict[str, str]:
    return {
        "results": f"{season}/results.json",
        "qualifying": f"{season}/qualifying.json",
        "sprint": f"{season}/sprint.json",
        "driverStandings": f"{season}/driverstandings.json",
        "constructorStandings": f"{season}/constructorstandings.json",
        "status": "status.json",
    }


def _round_endpoint_paths(season: int, round_number: int) -> dict[str, str]:
    return {
        "pitstops": f"{season}/{round_number}/pitstops.json",
        "laps": f"{season}/{round_number}/laps.json",
        "status": f"{season}/{round_number}/status.json",
    }


def _ok_status(fetched_at: datetime, connector_version: str) -> DataSourceStatus:
    return DataSourceStatus(
        source=JOLPICA_SOURCE,
        status="ok",
        severity="info",
        message="Jolpica season context fetched.",
        last_successful_sync_at=fetched_at,
        freshness="fresh",
        connector_version=connector_version,
        license_note=JOLPICA_LICENSE_NOTE,
    )


def _degraded_status(message: str, connector_version: str) -> DataSourceStatus:
    return DataSourceStatus(
        source=JOLPICA_SOURCE,
        status="degraded",
        severity="warning",
        message=message,
        freshness="unknown",
        connector_version=connector_version,
        license_note=JOLPICA_LICENSE_NOTE,
        action_required="Retry Jolpica sync or continue with local OpenF1/manual data.",
    )


def _request_path(path: str, *, limit: int = 100, offset: int = 0) -> str:
    return f"/{path}?{urlencode({'limit': str(limit), 'offset': str(offset)})}"


def _mrdata_int(payload: dict[str, Any], key: str) -> int:
    mrdata = payload.get("MRData")
    if not isinstance(mrdata, dict):
        return 0
    value = mrdata.get(key)
    return int(str(value or 0))


def _merge_pages(pages: list[dict[str, Any]]) -> dict[str, Any]:
    if not pages:
        return {"MRData": {"total": "0"}}
    merged = pages[0]
    for page in pages[1:]:
        _extend_races(merged, page)
        _extend_standings(merged, page)
        _extend_status(merged, page)
    if isinstance(merged.get("MRData"), dict):
        merged["MRData"]["offset"] = "0"
    return merged


def _extend_races(target: dict[str, Any], page: dict[str, Any]) -> None:
    target_races = _table_list(target, "RaceTable", "Races")
    page_races = _table_list(page, "RaceTable", "Races")
    target_races.extend(page_races)


def _extend_standings(target: dict[str, Any], page: dict[str, Any]) -> None:
    target_lists = _table_list(target, "StandingsTable", "StandingsLists")
    page_lists = _table_list(page, "StandingsTable", "StandingsLists")
    target_lists.extend(page_lists)


def _extend_status(target: dict[str, Any], page: dict[str, Any]) -> None:
    target_rows = _table_list(target, "StatusTable", "Status")
    page_rows = _table_list(page, "StatusTable", "Status")
    target_rows.extend(page_rows)


def _table_list(payload: dict[str, Any], table_key: str, list_key: str) -> list[Any]:
    mrdata = payload.get("MRData")
    table = mrdata.get(table_key) if isinstance(mrdata, dict) else None
    rows = table.get(list_key) if isinstance(table, dict) else None
    if isinstance(rows, list):
        return rows
    if isinstance(table, dict):
        empty: list[Any] = []
        table[list_key] = empty
        return empty
    return []


def _calendar_rounds(payload: dict[str, Any]) -> list[int]:
    races = _table_list(payload, "RaceTable", "Races")
    rounds: list[int] = []
    for race in races:
        if not isinstance(race, dict):
            continue
        try:
            rounds.append(int(str(race.get("round"))))
        except (TypeError, ValueError):
            continue
    return rounds


def _hash_payload(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def _snapshot_id(season: int, response_hash: str) -> str:
    return f"snapshot_jolpica_{season}_{response_hash[:12]}"
