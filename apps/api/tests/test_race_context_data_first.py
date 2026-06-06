from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from raceweek.api import data_first_routes
from raceweek.connectors.base import ConnectorResult
from raceweek.connectors.jolpica_normalize import JolpicaRace, JolpicaSeasonContext
from raceweek.connectors.openf1 import (
    OpenF1Meeting,
    OpenF1RaceControl,
    OpenF1Session,
    OpenF1SessionContext,
    OpenF1Weather,
)
from raceweek.core.models import DataSourceStatus, utc_now
from raceweek.main import app

client = TestClient(app)


def test_race_context_sync_persists_public_connector_rows(monkeypatch) -> None:
    client.post("/api/v1/data/reset", json={"scope": "all"})
    monkeypatch.setattr(data_first_routes, "OpenF1Connector", FakeOpenF1Connector)
    monkeypatch.setattr(data_first_routes, "JolpicaConnector", FakeJolpicaConnector)

    synced = client.post(
        "/api/v1/sync/race-context",
        json={"season": 2026, "meetingKey": "meeting_real_01"},
    ).json()

    assert synced["status"] == "ok"
    assert synced["rowCount"] >= 4
    assert {status["source"] for status in synced["statuses"]} == {"openf1", "jolpica"}

    current = client.get("/api/v1/race-context/current").json()
    sessions = client.get("/api/v1/race-context/meetings/meeting_real_01/sessions").json()
    freshness = client.get("/api/v1/data-freshness/race.current_meeting").json()
    app_status = client.get("/api/v1/app/status").json()

    assert current["item"]["meetingName"] == "Real Harbor Grand Prix"
    assert current["freshness"]["status"] == "real_current"
    assert sessions["items"][0]["sessionName"] == "Race"
    assert sessions["freshness"]["recordCount"] == 1
    assert freshness["status"] == "real_current"
    assert synced["currentEventId"] == "event_2026_08"
    assert app_status["currentEventId"] == "event_2026_08"


def test_current_race_context_falls_back_to_next_calendar_meeting() -> None:
    meeting = data_first_routes._current_or_next_race_meeting(
        [
            {
                "meetingKey": "jolpica_2026_1",
                "meetingName": "Australian Grand Prix",
                "startsAt": "2026-03-08T04:00:00+00:00",
            },
            {
                "meetingKey": "jolpica_2026_6",
                "meetingName": "Monaco Grand Prix",
                "startsAt": "2026-06-07T13:00:00+00:00",
            },
        ],
        "openf1_key_not_saved",
        now=datetime(2026, 6, 6, 12, tzinfo=UTC),
    )

    assert meeting is not None
    assert meeting["meetingName"] == "Monaco Grand Prix"


class FakeOpenF1Connector:
    async def fetch_session_context(
        self,
        meeting_key: str,
    ) -> ConnectorResult[OpenF1SessionContext]:
        fetched = utc_now()
        context = OpenF1SessionContext(
            meetings=[
                OpenF1Meeting(
                    meeting_key=meeting_key,
                    meeting_name="Real Harbor Grand Prix",
                    circuit_short_name="Harbor Circuit",
                    country_name="Exampleland",
                    location="Harbor",
                    year=2026,
                )
            ],
            sessions=[
                OpenF1Session(
                    session_key="session_real_race",
                    meeting_key=meeting_key,
                    session_name="Race",
                    session_type="Race",
                    date_start=datetime.fromisoformat("2026-06-07T18:00:00+00:00"),
                    date_end=datetime.fromisoformat("2026-06-07T20:00:00+00:00"),
                )
            ],
            weather=[
                OpenF1Weather(
                    session_key="session_real_race",
                    date=datetime.fromisoformat("2026-06-07T18:00:00+00:00"),
                    air_temperature=27,
                    track_temperature=39,
                    rainfall=0,
                    wind_speed=3,
                )
            ],
            race_control=[
                OpenF1RaceControl(
                    session_key="session_real_race",
                    category="Flag",
                    flag="GREEN",
                    message="Track clear.",
                    date=datetime.fromisoformat("2026-06-07T18:01:00+00:00"),
                )
            ],
        )
        return ConnectorResult(
            source="openf1",
            fetched_at=fetched,
            raw_snapshot_id="snapshot_openf1_real_01",
            data=context,
            status=DataSourceStatus(
                source="openf1",
                status="ok",
                severity="info",
                message="OpenF1 synced.",
                last_successful_sync_at=fetched,
                freshness="fresh",
                connector_version="openf1-test",
                license_note="Public test fixture",
            ),
            request_paths=["/sessions?meeting_key=meeting_real_01"],
            response_hash="hash-openf1",
            http_status=200,
            raw_payload={"ok": True},
        )


class FakeJolpicaConnector:
    async def fetch_season_context(self, season: int) -> ConnectorResult[JolpicaSeasonContext]:
        fetched = utc_now()
        context = JolpicaSeasonContext(
            races=[
                JolpicaRace(
                    season=season,
                    round_number=8,
                    race_name="Real Harbor Grand Prix",
                    circuit_id="harbor",
                    circuit_name="Harbor Circuit",
                    starts_at=datetime.fromisoformat("2026-06-07T18:00:00+00:00"),
                )
            ],
            race_results=[],
            qualifying_results=[],
            sprint_results=[],
            driver_standings=[],
            constructor_standings=[],
        )
        return ConnectorResult(
            source="jolpica",
            fetched_at=fetched,
            raw_snapshot_id="snapshot_jolpica_real_01",
            data=context,
            status=DataSourceStatus(
                source="jolpica",
                status="ok",
                severity="info",
                message="Jolpica synced.",
                last_successful_sync_at=fetched,
                freshness="fresh",
                connector_version="jolpica-test",
                license_note="Public test fixture",
            ),
            request_paths=["/2026.json?limit=100"],
            response_hash="hash-jolpica",
            http_status=200,
            raw_payload={"ok": True},
        )
