from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class JolpicaModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class JolpicaRace(JolpicaModel):
    season: int
    round_number: int
    race_name: str
    circuit_id: str | None = None
    circuit_name: str | None = None
    starts_at: datetime | None = None


class JolpicaResult(JolpicaModel):
    season: int
    round_number: int
    race_name: str
    session_type: Literal["race", "qualifying", "sprint"]
    position: int | None = None
    points: float | None = None
    driver_id: str | None = None
    driver_name: str | None = None
    constructor_id: str | None = None
    constructor_name: str | None = None


class JolpicaStanding(JolpicaModel):
    standing_type: Literal["driver", "constructor"]
    season: int
    round_number: int | None = None
    position: int
    points: float
    wins: int
    driver_id: str | None = None
    driver_name: str | None = None
    constructor_id: str | None = None
    constructor_name: str | None = None


class JolpicaSeasonContext(JolpicaModel):
    races: list[JolpicaRace]
    race_results: list[JolpicaResult]
    qualifying_results: list[JolpicaResult]
    sprint_results: list[JolpicaResult]
    driver_standings: list[JolpicaStanding]
    constructor_standings: list[JolpicaStanding]


def normalize_context(raw_payload: dict[str, object]) -> JolpicaSeasonContext:
    return JolpicaSeasonContext(
        races=parse_races(raw_payload["calendar"]),
        race_results=parse_results(raw_payload["results"], "Results", "race"),
        qualifying_results=parse_results(
            raw_payload["qualifying"],
            "QualifyingResults",
            "qualifying",
        ),
        sprint_results=parse_results(raw_payload["sprint"], "SprintResults", "sprint"),
        driver_standings=parse_driver_standings(raw_payload["driverStandings"]),
        constructor_standings=parse_constructor_standings(raw_payload["constructorStandings"]),
    )


def empty_context() -> JolpicaSeasonContext:
    return JolpicaSeasonContext(
        races=[],
        race_results=[],
        qualifying_results=[],
        sprint_results=[],
        driver_standings=[],
        constructor_standings=[],
    )


def parse_races(payload: object) -> list[JolpicaRace]:
    return [
        JolpicaRace(
            season=_int(row.get("season")),
            round_number=_int(row.get("round")),
            race_name=str(row.get("raceName") or "Unknown race"),
            circuit_id=_nested_str(row, "Circuit", "circuitId"),
            circuit_name=_nested_str(row, "Circuit", "circuitName"),
            starts_at=_datetime(row.get("date"), row.get("time")),
        )
        for row in _race_rows(payload)
    ]


def parse_results(
    payload: object,
    result_key: str,
    session_type: Literal["race", "qualifying", "sprint"],
) -> list[JolpicaResult]:
    items: list[JolpicaResult] = []
    for race in _race_rows(payload):
        for row in _list(row_value=race.get(result_key)):
            items.append(
                JolpicaResult(
                    season=_int(race.get("season")),
                    round_number=_int(race.get("round")),
                    race_name=str(race.get("raceName") or "Unknown race"),
                    session_type=session_type,
                    position=_optional_int(row.get("position")),
                    points=_optional_float(row.get("points")),
                    driver_id=_nested_str(row, "Driver", "driverId"),
                    driver_name=_driver_name(row.get("Driver")),
                    constructor_id=_nested_str(row, "Constructor", "constructorId"),
                    constructor_name=_nested_str(row, "Constructor", "name"),
                )
            )
    return items


def parse_driver_standings(payload: object) -> list[JolpicaStanding]:
    standings: list[JolpicaStanding] = []
    for table in _standing_lists(payload):
        for row in _list(row_value=table.get("DriverStandings")):
            constructors = _list(row_value=row.get("Constructors"))
            constructor = constructors[0] if constructors else {}
            standings.append(
                JolpicaStanding(
                    standing_type="driver",
                    season=_int(table.get("season")),
                    round_number=_optional_int(table.get("round")),
                    position=_int(row.get("position")),
                    points=_float(row.get("points")),
                    wins=_int(row.get("wins")),
                    driver_id=_nested_str(row, "Driver", "driverId"),
                    driver_name=_driver_name(row.get("Driver")),
                    constructor_id=_str_or_none(constructor.get("constructorId")),
                    constructor_name=_str_or_none(constructor.get("name")),
                )
            )
    return standings


def parse_constructor_standings(payload: object) -> list[JolpicaStanding]:
    standings: list[JolpicaStanding] = []
    for table in _standing_lists(payload):
        for row in _list(row_value=table.get("ConstructorStandings")):
            standings.append(
                JolpicaStanding(
                    standing_type="constructor",
                    season=_int(table.get("season")),
                    round_number=_optional_int(table.get("round")),
                    position=_int(row.get("position")),
                    points=_float(row.get("points")),
                    wins=_int(row.get("wins")),
                    constructor_id=_nested_str(row, "Constructor", "constructorId"),
                    constructor_name=_nested_str(row, "Constructor", "name"),
                )
            )
    return standings


def _race_rows(payload: object) -> list[dict[str, Any]]:
    mrdata = payload.get("MRData") if isinstance(payload, dict) else None
    race_table = mrdata.get("RaceTable") if isinstance(mrdata, dict) else None
    return _list(race_table.get("Races") if isinstance(race_table, dict) else None)


def _standing_lists(payload: object) -> list[dict[str, Any]]:
    mrdata = payload.get("MRData") if isinstance(payload, dict) else None
    table = mrdata.get("StandingsTable") if isinstance(mrdata, dict) else None
    return _list(table.get("StandingsLists") if isinstance(table, dict) else None)


def _list(row_value: object) -> list[dict[str, Any]]:
    if not isinstance(row_value, list):
        return []
    return [item for item in row_value if isinstance(item, dict)]


def _nested_str(payload: dict[str, Any], parent: str, key: str) -> str | None:
    nested = payload.get(parent)
    return _str_or_none(nested.get(key)) if isinstance(nested, dict) else None


def _driver_name(value: object) -> str | None:
    if not isinstance(value, dict):
        return None
    parts = [
        _str_or_none(value.get("givenName")),
        _str_or_none(value.get("familyName")),
    ]
    return " ".join(part for part in parts if part) or None


def _datetime(date_value: object, time_value: object) -> datetime | None:
    if not date_value:
        return None
    raw = str(date_value)
    if time_value:
        raw = f"{raw}T{time_value}"
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def _int(value: object) -> int:
    return int(str(value))


def _optional_int(value: object) -> int | None:
    return None if value in {None, ""} else _int(value)


def _float(value: object) -> float:
    return float(str(value))


def _optional_float(value: object) -> float | None:
    return None if value in {None, ""} else _float(value)


def _str_or_none(value: object) -> str | None:
    return None if value in {None, ""} else str(value)
