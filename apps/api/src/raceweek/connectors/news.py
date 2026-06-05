from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, ConfigDict

from raceweek.connectors.base import ConnectorResult
from raceweek.core.models import DataSourceStatus, utc_now

NEWS_SOURCE = "news"
NEWS_CONNECTOR_VERSION = "rss-news-v1"
NEWS_LICENSE_NOTE = "RSS/Atom metadata and feed-provided summaries only."


class NewsModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class NewsItem(NewsModel):
    news_id: str
    source_name: str
    title: str
    url: str | None = None
    published_at: datetime | None = None
    retrieved_at: datetime
    summary: str
    entities: list[str]
    risk_flags: list[str]
    license_note: str = NEWS_LICENSE_NOTE


class NewsFeedResult(NewsModel):
    items: list[NewsItem]


class NewsConnector:
    def __init__(
        self,
        *,
        client: httpx.AsyncClient | None = None,
        connector_version: str = NEWS_CONNECTOR_VERSION,
    ) -> None:
        self.client = client or httpx.AsyncClient()
        self.connector_version = connector_version

    async def fetch_rss_feed(
        self,
        *,
        source_name: str,
        feed_url: str,
    ) -> ConnectorResult[NewsFeedResult]:
        fetched_at = utc_now()
        request_paths = [_request_path(feed_url)]
        http_status: int | None = None
        try:
            response = await self.client.get(feed_url)
            http_status = response.status_code
            if response.status_code >= 400:
                raise NewsConnectorError(
                    f"News feed request failed: HTTP {response.status_code}",
                    status_code=response.status_code,
                )
            items = _parse_feed(response.text, source_name, fetched_at)
            data = NewsFeedResult(items=items)
            metadata_payload = data.model_dump(by_alias=True, mode="json")
            response_hash = _hash_payload(metadata_payload)
            return ConnectorResult(
                source=NEWS_SOURCE,
                fetched_at=fetched_at,
                raw_snapshot_id=_snapshot_id(source_name, response_hash),
                data=data,
                status=_ok_status(fetched_at, self.connector_version),
                request_paths=request_paths,
                response_hash=response_hash,
                http_status=http_status,
                raw_payload=metadata_payload,
            )
        except (httpx.HTTPError, NewsConnectorError, ET.ParseError) as exc:
            if isinstance(exc, NewsConnectorError) and exc.status_code is not None:
                http_status = exc.status_code
            error_payload: dict[str, object] = {"error": str(exc), "items": []}
            response_hash = _hash_payload(error_payload)
            return ConnectorResult(
                source=NEWS_SOURCE,
                fetched_at=fetched_at,
                raw_snapshot_id=_snapshot_id(source_name, response_hash),
                data=NewsFeedResult(items=[]),
                status=_degraded_status(str(exc), self.connector_version),
                request_paths=request_paths,
                response_hash=response_hash,
                http_status=http_status,
                raw_payload=error_payload,
            )


class NewsConnectorError(ValueError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _parse_feed(xml_text: str, source_name: str, retrieved_at: datetime) -> list[NewsItem]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise NewsConnectorError("News feed must be valid RSS/Atom XML") from exc
    rss_items = root.findall("./channel/item")
    atom_items = root.findall("{http://www.w3.org/2005/Atom}entry")
    return [
        _item_from_rss(item, source_name, retrieved_at)
        for item in rss_items
    ] + [
        _item_from_atom(item, source_name, retrieved_at)
        for item in atom_items
    ]


def _item_from_rss(element: ET.Element, source_name: str, retrieved_at: datetime) -> NewsItem:
    title = _child_text(element, "title") or "Untitled"
    url = _child_text(element, "link")
    summary = _summary(_child_text(element, "description"))
    published = _parse_datetime(_child_text(element, "pubDate"))
    return _news_item(title, url, summary, published, source_name, retrieved_at)


def _item_from_atom(element: ET.Element, source_name: str, retrieved_at: datetime) -> NewsItem:
    ns = "{http://www.w3.org/2005/Atom}"
    title = _child_text(element, f"{ns}title") or "Untitled"
    link = element.find(f"{ns}link")
    url = link.attrib.get("href") if link is not None else None
    summary = _summary(_child_text(element, f"{ns}summary"))
    published = _parse_datetime(
        _child_text(element, f"{ns}published") or _child_text(element, f"{ns}updated")
    )
    return _news_item(title, url, summary, published, source_name, retrieved_at)


def _news_item(
    title: str,
    url: str | None,
    summary: str,
    published_at: datetime | None,
    source_name: str,
    retrieved_at: datetime,
) -> NewsItem:
    text = f"{title} {summary}"
    return NewsItem(
        news_id=_item_id(url or title),
        source_name=source_name,
        title=title,
        url=url,
        published_at=published_at,
        retrieved_at=retrieved_at,
        summary=summary,
        entities=_entities(text),
        risk_flags=_risk_flags(text),
    )


def _child_text(element: ET.Element, tag: str) -> str | None:
    child = element.find(tag)
    if child is None or child.text is None:
        return None
    return child.text.strip()


def _summary(value: str | None) -> str:
    clean = re.sub(r"<[^>]+>", "", value or "").strip()
    return clean[:280]


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return parsedate_to_datetime(value)


def _entities(text: str) -> list[str]:
    entities = []
    for match in re.finditer(r"\bDriver ([A-Z][a-z]+)\b", text):
        entities.append(f"driver:{match.group(1).lower()}")
    for match in re.finditer(r"\bConstructor ([A-Z][a-z]+)\b", text):
        entities.append(f"constructor:{match.group(1).lower()}")
    return sorted(set(entities))


def _risk_flags(text: str) -> list[str]:
    lowered = text.lower()
    flags = []
    if "grid penalty" in lowered:
        flags.append("grid_penalty")
    if "reliability" in lowered:
        flags.append("reliability")
    if "upgrade" in lowered:
        flags.append("upgrade")
    return flags


def _ok_status(fetched_at: datetime, connector_version: str) -> DataSourceStatus:
    return DataSourceStatus(
        source=NEWS_SOURCE,
        status="ok",
        severity="info",
        message="News feed metadata fetched.",
        last_successful_sync_at=fetched_at,
        freshness="fresh",
        connector_version=connector_version,
        license_note=NEWS_LICENSE_NOTE,
    )


def _degraded_status(message: str, connector_version: str) -> DataSourceStatus:
    return DataSourceStatus(
        source=NEWS_SOURCE,
        status="degraded",
        severity="warning",
        message=message,
        freshness="unknown",
        connector_version=connector_version,
        license_note=NEWS_LICENSE_NOTE,
        action_required="Retry the news feed or continue with existing/manual news notes.",
    )


def _request_path(feed_url: str) -> str:
    parsed = urlparse(feed_url)
    return parsed.path or "/"


def _hash_payload(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def _item_id(value: str) -> str:
    return f"news_{hashlib.sha256(value.encode()).hexdigest()[:16]}"


def _snapshot_id(source_name: str, response_hash: str) -> str:
    safe_source = "".join(char if char.isalnum() else "_" for char in source_name.lower())
    return f"snapshot_news_{safe_source}_{response_hash[:12]}"
