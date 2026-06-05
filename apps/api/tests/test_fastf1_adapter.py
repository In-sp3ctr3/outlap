from __future__ import annotations

from pathlib import Path

from raceweek.connectors.fastf1_adapter import FastF1Adapter, FastF1SessionSummary


def test_fastf1_adapter_enables_cache_and_returns_aggregates(tmp_path: Path) -> None:
    fake = FakeFastF1()
    adapter = FastF1Adapter(cache_path=tmp_path / "fastf1-cache", library=fake)

    result = adapter.load_session_summary(2026, "Harbor Night Grand Prix", "R")

    assert fake.cache_paths == [str(tmp_path / "fastf1-cache")]
    assert fake.session.loaded_with == {"laps": True, "telemetry": False, "weather": True}
    assert result.status.source == "fastf1"
    assert result.status.status == "ok"
    assert result.request_paths == ["fastf1://2026/Harbor Night Grand Prix/R"]
    assert result.http_status is None
    assert isinstance(result.data, FastF1SessionSummary)
    assert result.data.event_name == "Harbor Night Grand Prix"
    assert result.data.session_name == "Race"
    assert result.data.lap_count == 3
    assert result.data.result_count == 2
    assert result.data.weather_sample_count == 2
    assert "telemetry" not in result.raw_payload


def test_fastf1_adapter_reports_disabled_when_dependency_missing(tmp_path: Path) -> None:
    adapter = FastF1Adapter(cache_path=tmp_path / "fastf1-cache", library=None)

    result = adapter.load_session_summary(2026, "Harbor Night Grand Prix", "R")

    assert result.status.status == "disabled"
    assert "FastF1 is not installed" in result.status.message
    assert result.data.lap_count == 0


class FakeFastF1:
    def __init__(self) -> None:
        self.cache_paths: list[str] = []
        self.Cache = FakeCache(self)
        self.session = FakeSession()

    def get_session(self, season: int, grand_prix: str, session_name: str) -> FakeSession:
        self.session.request = {
            "season": season,
            "grand_prix": grand_prix,
            "session_name": session_name,
        }
        return self.session


class FakeCache:
    def __init__(self, parent: FakeFastF1) -> None:
        self.parent = parent

    def enable_cache(self, cache_path: str) -> None:
        self.parent.cache_paths.append(cache_path)


class FakeSession:
    def __init__(self) -> None:
        self.event = {"EventName": "Harbor Night Grand Prix"}
        self.name = "Race"
        self.laps = [object(), object(), object()]
        self.results = [object(), object()]
        self.weather_data = [object(), object()]
        self.loaded_with: dict[str, bool] = {}
        self.request: dict[str, object] = {}

    def load(self, *, laps: bool, telemetry: bool, weather: bool) -> None:
        self.loaded_with = {"laps": laps, "telemetry": telemetry, "weather": weather}
