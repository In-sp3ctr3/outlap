from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path

import httpx

from raceweek.connectors.base import ConnectorResult
from raceweek.connectors.news import NEWS_LICENSE_NOTE, NewsConnector, NewsFeedResult
from raceweek.storage.jsonio import load_json_value
from raceweek.storage.repository import DuckDbRepository

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "packages" / "fixtures"
Handler = Callable[[httpx.Request], httpx.Response]


def test_news_connector_keeps_metadata_only() -> None:
    feed_xml = (FIXTURES / "rss_news_demo.xml").read_text()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=feed_xml)

    result = asyncio.run(fetch_feed(handler))

    assert result.status.source == "news"
    assert result.status.status == "ok"
    assert result.request_paths == ["/rss.xml"]
    assert len(result.response_hash) == 64
    assert len(result.data.items) == 2
    assert result.data.items[0].title == "Driver Alpha faces grid penalty review"
    assert result.data.items[0].summary.startswith("Short feed summary")
    assert result.data.items[0].risk_flags == ["grid_penalty"]
    assert "driver:alpha" in result.data.items[0].entities
    assert "Full article body" not in str(result.raw_payload)
    assert "content:encoded" not in str(result.raw_payload)


def test_news_connector_degrades_on_invalid_feed() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<rss><broken></rss>")

    result = asyncio.run(fetch_feed(handler))

    assert result.status.status == "degraded"
    assert "valid RSS/Atom XML" in result.status.message
    assert result.data.items == []
    assert result.http_status == 200


def test_news_connector_result_persists_metadata_snapshot(tmp_path: Path) -> None:
    feed_xml = (FIXTURES / "rss_news_demo.xml").read_text()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=feed_xml)

    result = asyncio.run(fetch_feed(handler))
    repository = DuckDbRepository(tmp_path / "raceweek.duckdb")

    repository.save_connector_result(
        result,
        request_url_template="https://news.example.test/rss.xml",
        license_note=NEWS_LICENSE_NOTE,
        normalization_version="rss-news-normalizer-v1",
    )

    with repository.connect() as connection:
        row = connection.execute(
            """
            SELECT source_name, raw_json, content_hash, status
            FROM source_snapshots
            WHERE snapshot_id = ?
            """,
            [result.raw_snapshot_id],
        ).fetchone()

    assert row is not None
    assert row[0] == "news"
    assert row[2] == result.response_hash
    assert row[3] == "ok"
    raw = load_json_value(row[1])
    assert raw["items"][0]["title"] == "Driver Alpha faces grid penalty review"
    assert "Full article body" not in str(raw)


async def fetch_feed(handler: Handler) -> ConnectorResult[NewsFeedResult]:
    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        connector = NewsConnector(client=client)
        return await connector.fetch_rss_feed(
            source_name="Demo Motorsport Wire",
            feed_url="https://news.example.test/rss.xml?token=secret",
        )
