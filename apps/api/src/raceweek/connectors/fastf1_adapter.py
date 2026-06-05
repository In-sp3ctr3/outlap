from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from raceweek.connectors.base import ConnectorResult
from raceweek.core.models import DataSourceStatus, utc_now

FASTF1_SOURCE = "fastf1"
FASTF1_CONNECTOR_VERSION = "fastf1-adapter-v1"
FASTF1_LICENSE_NOTE = "FastF1 local cache adapter; aggregated session metadata only."
_AUTO_LOAD = object()


class FastF1Model(BaseModel):
    model_config = ConfigDict(extra="ignore")


class FastF1SessionSummary(FastF1Model):
    season: int
    grand_prix: str
    session_code: str
    event_name: str
    session_name: str
    lap_count: int
    result_count: int
    weather_sample_count: int


class FastF1Adapter:
    def __init__(
        self,
        *,
        cache_path: str | Path,
        library: Any = _AUTO_LOAD,
        connector_version: str = FASTF1_CONNECTOR_VERSION,
    ) -> None:
        self.cache_path = Path(cache_path)
        self.library = _load_fastf1() if library is _AUTO_LOAD else library
        self.connector_version = connector_version

    def load_session_summary(
        self,
        season: int,
        grand_prix: str,
        session_name: str,
    ) -> ConnectorResult[FastF1SessionSummary]:
        fetched_at = utc_now()
        request_paths = [f"fastf1://{season}/{grand_prix}/{session_name}"]
        if self.library is None:
            return self._disabled_result(
                season,
                grand_prix,
                session_name,
                fetched_at,
                request_paths,
            )

        try:
            self.cache_path.mkdir(parents=True, exist_ok=True)
            self.library.Cache.enable_cache(str(self.cache_path))
            session = self.library.get_session(season, grand_prix, session_name)
            session.load(laps=True, telemetry=False, weather=True)
            summary = _summary_from_session(session, season, grand_prix, session_name)
            raw_payload = summary.model_dump(by_alias=True, mode="json")
            response_hash = _hash_payload(raw_payload)
            return ConnectorResult(
                source=FASTF1_SOURCE,
                fetched_at=fetched_at,
                raw_snapshot_id=_snapshot_id(season, grand_prix, session_name, response_hash),
                data=summary,
                status=_ok_status(fetched_at, self.connector_version),
                request_paths=request_paths,
                response_hash=response_hash,
                http_status=None,
                raw_payload=raw_payload,
            )
        except Exception as exc:
            return self._degraded_result(
                season,
                grand_prix,
                session_name,
                fetched_at,
                request_paths,
                str(exc),
            )

    def _disabled_result(
        self,
        season: int,
        grand_prix: str,
        session_name: str,
        fetched_at: Any,
        request_paths: list[str],
    ) -> ConnectorResult[FastF1SessionSummary]:
        summary = _empty_summary(season, grand_prix, session_name)
        raw_payload = summary.model_dump(by_alias=True, mode="json")
        response_hash = _hash_payload(raw_payload)
        return ConnectorResult(
            source=FASTF1_SOURCE,
            fetched_at=fetched_at,
            raw_snapshot_id=_snapshot_id(season, grand_prix, session_name, response_hash),
            data=summary,
            status=_disabled_status(self.connector_version),
            request_paths=request_paths,
            response_hash=response_hash,
            http_status=None,
            raw_payload=raw_payload,
        )

    def _degraded_result(
        self,
        season: int,
        grand_prix: str,
        session_name: str,
        fetched_at: Any,
        request_paths: list[str],
        message: str,
    ) -> ConnectorResult[FastF1SessionSummary]:
        summary = _empty_summary(season, grand_prix, session_name)
        raw_payload = {"error": message, **summary.model_dump(by_alias=True, mode="json")}
        response_hash = _hash_payload(raw_payload)
        return ConnectorResult(
            source=FASTF1_SOURCE,
            fetched_at=fetched_at,
            raw_snapshot_id=_snapshot_id(season, grand_prix, session_name, response_hash),
            data=summary,
            status=_degraded_status(message, self.connector_version),
            request_paths=request_paths,
            response_hash=response_hash,
            http_status=None,
            raw_payload=raw_payload,
        )


def _load_fastf1() -> Any | None:
    try:
        return importlib.import_module("fastf1")
    except ImportError:
        return None


def _summary_from_session(
    session: Any,
    season: int,
    grand_prix: str,
    session_code: str,
) -> FastF1SessionSummary:
    event = getattr(session, "event", {})
    return FastF1SessionSummary(
        season=season,
        grand_prix=grand_prix,
        session_code=session_code,
        event_name=_mapping_get(event, "EventName") or grand_prix,
        session_name=str(getattr(session, "name", session_code)),
        lap_count=_count(getattr(session, "laps", [])),
        result_count=_count(getattr(session, "results", [])),
        weather_sample_count=_count(getattr(session, "weather_data", [])),
    )


def _empty_summary(season: int, grand_prix: str, session_code: str) -> FastF1SessionSummary:
    return FastF1SessionSummary(
        season=season,
        grand_prix=grand_prix,
        session_code=session_code,
        event_name=grand_prix,
        session_name=session_code,
        lap_count=0,
        result_count=0,
        weather_sample_count=0,
    )


def _ok_status(fetched_at: Any, connector_version: str) -> DataSourceStatus:
    return DataSourceStatus(
        source=FASTF1_SOURCE,
        status="ok",
        severity="info",
        message="FastF1 session summary loaded from local cache adapter.",
        last_successful_sync_at=fetched_at,
        freshness="fresh",
        connector_version=connector_version,
        license_note=FASTF1_LICENSE_NOTE,
    )


def _disabled_status(connector_version: str) -> DataSourceStatus:
    return DataSourceStatus(
        source=FASTF1_SOURCE,
        status="disabled",
        severity="warning",
        message="FastF1 is not installed; Jolpica/OpenF1 fallback remains available.",
        freshness="unknown",
        connector_version=connector_version,
        license_note=FASTF1_LICENSE_NOTE,
        action_required=(
            "Install the optional FastF1 dependency to enable cached session summaries."
        ),
    )


def _degraded_status(message: str, connector_version: str) -> DataSourceStatus:
    return DataSourceStatus(
        source=FASTF1_SOURCE,
        status="degraded",
        severity="warning",
        message=f"FastF1 session summary failed: {message}",
        freshness="unknown",
        connector_version=connector_version,
        license_note=FASTF1_LICENSE_NOTE,
        action_required="Retry FastF1 cache loading or use Jolpica/OpenF1 fallback data.",
    )


def _mapping_get(value: Any, key: str) -> str | None:
    if isinstance(value, dict):
        found = value.get(key)
        return None if found is None else str(found)
    try:
        found = value[key]
    except Exception:
        return None
    return None if found is None else str(found)


def _count(value: Any) -> int:
    try:
        return len(value)
    except TypeError:
        return 0


def _hash_payload(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def _snapshot_id(season: int, grand_prix: str, session_name: str, response_hash: str) -> str:
    raw_key = f"{season}_{grand_prix}_{session_name}".lower()
    safe_key = "".join(char if char.isalnum() else "_" for char in raw_key)
    return f"snapshot_fastf1_{safe_key}_{response_hash[:12]}"
