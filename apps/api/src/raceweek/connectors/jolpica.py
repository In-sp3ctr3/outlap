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
            for key, path in _endpoint_paths(season).items():
                payload, http_status = await self._get(path)
                raw_payload[key] = payload
                request_paths.append(_request_path(path))
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
        response = await self.client.get(f"{self.base_url}/{path}", params={"limit": "100"})
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


def _endpoint_paths(season: int) -> dict[str, str]:
    return {
        "calendar": f"{season}.json",
        "results": f"{season}/results.json",
        "qualifying": f"{season}/qualifying.json",
        "sprint": f"{season}/sprint.json",
        "driverStandings": f"{season}/driverstandings.json",
        "constructorStandings": f"{season}/constructorstandings.json",
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


def _request_path(path: str) -> str:
    return f"/{path}?{urlencode({'limit': '100'})}"


def _hash_payload(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def _snapshot_id(season: int, response_hash: str) -> str:
    return f"snapshot_jolpica_{season}_{response_hash[:12]}"
