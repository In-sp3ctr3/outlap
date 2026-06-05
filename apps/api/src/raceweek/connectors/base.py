from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from raceweek.core.models import DataSourceStatus


@dataclass(frozen=True)
class ConnectorResult[T]:
    source: str
    fetched_at: datetime
    raw_snapshot_id: str
    data: T
    status: DataSourceStatus
    request_paths: list[str]
    response_hash: str
    http_status: int | None
    raw_payload: dict[str, object]
