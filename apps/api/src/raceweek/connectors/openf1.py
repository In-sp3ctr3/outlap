from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError

from raceweek.connectors.base import ConnectorResult
from raceweek.core.models import DataSourceStatus, utc_now

OPENF1_SOURCE = "openf1"
OPENF1_CONNECTOR_VERSION = "openf1-v1"
OPENF1_LICENSE_NOTE = "OpenF1 public API; unofficial Formula 1 data source."


class OpenF1Model(BaseModel):
    model_config = ConfigDict(extra="ignore")


class OpenF1Meeting(OpenF1Model):
    meeting_key: str | int
    meeting_name: str | None = None
    circuit_short_name: str | None = None
    country_name: str | None = None
    location: str | None = None
    year: int | None = None


class OpenF1Session(OpenF1Model):
    session_key: str | int
    meeting_key: str | int
    session_name: str
    session_type: str
    date_start: datetime | None = None
    date_end: datetime | None = None


class OpenF1Weather(OpenF1Model):
    session_key: str | int
    date: datetime | None = None
    air_temperature: float | None = None
    track_temperature: float | None = None
    rainfall: float | None = None
    wind_speed: float | None = None


class OpenF1RaceControl(OpenF1Model):
    session_key: str | int | None = None
    category: str | None = None
    flag: str | None = None
    message: str
    date: datetime | None = None


class OpenF1SessionContext(OpenF1Model):
    meetings: list[OpenF1Meeting]
    sessions: list[OpenF1Session]
    weather: list[OpenF1Weather]
    race_control: list[OpenF1RaceControl]


class OpenF1Connector:
    def __init__(
        self,
        *,
        base_url: str = "https://api.openf1.org/v1",
        client: httpx.AsyncClient | None = None,
        connector_version: str = OPENF1_CONNECTOR_VERSION,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.AsyncClient()
        self.connector_version = connector_version

    async def fetch_session_context(
        self,
        meeting_key: str,
    ) -> ConnectorResult[OpenF1SessionContext]:
        fetched_at = utc_now()
        raw_payload: dict[str, object] = {}
        request_paths: list[str] = []
        http_status: int | None = 200
        try:
            for endpoint in ["meetings", "sessions", "weather", "race_control"]:
                payload, http_status = await self._get(endpoint, {"meeting_key": meeting_key})
                raw_payload[endpoint] = payload
                request_paths.append(_request_path(endpoint, {"meeting_key": meeting_key}))
            context = OpenF1SessionContext(
                meetings=_validate_list(OpenF1Meeting, raw_payload["meetings"]),
                sessions=_validate_list(OpenF1Session, raw_payload["sessions"]),
                weather=_validate_list(OpenF1Weather, raw_payload["weather"]),
                race_control=_validate_list(OpenF1RaceControl, raw_payload["race_control"]),
            )
            response_hash = _hash_payload(raw_payload)
            return ConnectorResult(
                source=OPENF1_SOURCE,
                fetched_at=fetched_at,
                raw_snapshot_id=_snapshot_id(meeting_key, response_hash),
                data=context,
                status=_ok_status(fetched_at, self.connector_version),
                request_paths=request_paths,
                response_hash=response_hash,
                http_status=http_status,
                raw_payload=raw_payload,
            )
        except (httpx.HTTPError, OpenF1ConnectorError, ValidationError, ValueError) as exc:
            http_status = exc.status_code if isinstance(exc, OpenF1ConnectorError) else None
            failed_endpoint = _request_path(
                endpoint if "endpoint" in locals() else "unknown",
                {"meeting_key": meeting_key},
            )
            if not request_paths or request_paths[-1] != failed_endpoint:
                request_paths.append(failed_endpoint)
            raw_payload = raw_payload or {"error": str(exc)}
            response_hash = _hash_payload(raw_payload)
            return ConnectorResult(
                source=OPENF1_SOURCE,
                fetched_at=fetched_at,
                raw_snapshot_id=_snapshot_id(meeting_key, response_hash),
                data=OpenF1SessionContext(meetings=[], sessions=[], weather=[], race_control=[]),
                status=_degraded_status(str(exc), self.connector_version),
                request_paths=request_paths,
                response_hash=response_hash,
                http_status=http_status,
                raw_payload=raw_payload,
            )

    async def _get(
        self,
        endpoint: str,
        params: dict[str, str],
    ) -> tuple[list[dict[str, Any]], int]:
        response = await self.client.get(f"{self.base_url}/{endpoint}", params=params)
        if response.status_code >= 400:
            raise OpenF1ConnectorError(
                f"OpenF1 request failed for /{endpoint}: HTTP {response.status_code}",
                status_code=response.status_code,
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise OpenF1ConnectorError(
                f"OpenF1 /{endpoint} response must be valid JSON",
                status_code=response.status_code,
            ) from exc
        if not isinstance(payload, list):
            raise OpenF1ConnectorError(
                f"OpenF1 /{endpoint} response must be a list",
                status_code=response.status_code,
            )
        return [item for item in payload if isinstance(item, dict)], response.status_code


class OpenF1ConnectorError(ValueError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _validate_list[ModelT: BaseModel](
    model: type[ModelT],
    payload: object,
) -> list[ModelT]:
    if not isinstance(payload, list):
        raise OpenF1ConnectorError("OpenF1 normalized payload must be a list")
    return [model.model_validate(item) for item in payload]


def _ok_status(fetched_at: datetime, connector_version: str) -> DataSourceStatus:
    return DataSourceStatus(
        source=OPENF1_SOURCE,
        status="ok",
        severity="info",
        message="OpenF1 race-week context fetched.",
        last_successful_sync_at=fetched_at,
        freshness="fresh",
        connector_version=connector_version,
        license_note=OPENF1_LICENSE_NOTE,
    )


def _degraded_status(message: str, connector_version: str) -> DataSourceStatus:
    return DataSourceStatus(
        source=OPENF1_SOURCE,
        status="degraded",
        severity="warning",
        message=message,
        freshness="unknown",
        connector_version=connector_version,
        license_note=OPENF1_LICENSE_NOTE,
        action_required="Retry OpenF1 sync or continue with the latest local snapshot.",
    )


def _request_path(endpoint: str, params: dict[str, str]) -> str:
    return f"/{endpoint}?{urlencode(params)}"


def _hash_payload(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def _snapshot_id(meeting_key: str, response_hash: str) -> str:
    safe_key = "".join(char if char.isalnum() else "_" for char in meeting_key)
    return f"snapshot_openf1_{safe_key}_{response_hash[:12]}"
