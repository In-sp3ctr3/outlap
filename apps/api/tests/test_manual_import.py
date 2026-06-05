from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from raceweek.main import app

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "packages" / "fixtures"
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_demo_state() -> None:
    client.post("/api/v1/demo/reset")


def load_fixture(name: str) -> dict[str, object]:
    with (FIXTURES / name).open() as file:
        payload: dict[str, object] = json.load(file)
    return payload


def test_team_import_warns_on_unknown_fields_and_persists() -> None:
    payload = load_fixture("fantasy_team_demo.json")
    payload["ignoredTopLevel"] = True
    first_asset = payload["assets"][0]
    assert isinstance(first_asset, dict)
    first_asset["ignoredNested"] = "warn"

    response = client.post("/api/v1/fantasy/import/team", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["itemCount"] == 7
    assert body["sourceSnapshotId"] == "snapshot_demo_team_01"
    assert any("ignoredTopLevel" in warning for warning in body["warnings"])
    assert any("ignoredNested" in warning for warning in body["warnings"])
    current = client.get("/api/v1/fantasy/teams/current").json()["items"][0]
    assert current["teamSnapshotId"] == "team_demo_01"


def test_team_import_rejects_duplicate_lineup_assets() -> None:
    payload = load_fixture("fantasy_team_demo.json")
    assets = payload["assets"]
    assert isinstance(assets, list)
    assert isinstance(assets[0], dict)
    assert isinstance(assets[1], dict)
    assets[1]["assetId"] = assets[0]["assetId"]

    response = client.post("/api/v1/fantasy/import/team", json=payload)

    assert response.status_code == 422
    assert "duplicate" in response.json()["detail"]


def test_team_csv_import_computes_budget_from_market() -> None:
    body = {
        "format": "csv",
        "teamSnapshotId": "team_csv",
        "teamName": "CSV Team",
        "eventId": "event_demo_01",
        "costCapMillions": "100",
        "freeTransfers": "2",
        "capturedAt": "2026-06-05T00:00:00Z",
        "content": _csv(
            [
                {"assetId": "asset_driver_alpha", "assetType": "driver", "boostMultiplier": "2"},
                {"assetId": "asset_driver_bravo", "assetType": "driver", "boostMultiplier": "1"},
                {"assetId": "asset_driver_charlie", "assetType": "driver", "boostMultiplier": "1"},
                {"assetId": "asset_driver_delta", "assetType": "driver", "boostMultiplier": "1"},
                {"assetId": "asset_driver_echo", "assetType": "driver", "boostMultiplier": "1"},
                {
                    "assetId": "asset_constructor_two",
                    "assetType": "constructor",
                    "boostMultiplier": "1",
                },
                {
                    "assetId": "asset_constructor_three",
                    "assetType": "constructor",
                    "boostMultiplier": "1",
                },
            ],
            ["assetId", "assetType", "boostMultiplier"],
        ),
    }

    response = client.post("/api/v1/fantasy/import/team", json=body)

    assert response.status_code == 201
    team = client.get("/api/v1/fantasy/teams/current").json()["items"][0]
    assert team["teamSnapshotId"] == "team_csv"
    assert team["budgetUsedMillions"] == 99


def test_market_csv_import_validates_prices_and_updates_assets() -> None:
    bad = {
        "format": "csv",
        "eventId": "event_csv",
        "content": "assetId,assetType,displayName,priceMillions\nbad,driver,Bad Driver,nope\n",
    }
    assert client.post("/api/v1/fantasy/import/market", json=bad).status_code == 422

    good = {
        "format": "csv",
        "eventId": "event_csv",
        "content": _csv(
            [
                {
                    "assetId": "csv_driver_one",
                    "assetType": "driver",
                    "displayName": "CSV Driver One",
                    "priceMillions": "12.5",
                    "ownershipPct": "3.2",
                    "unknownColumn": "ignored",
                },
                {
                    "assetId": "csv_constructor_one",
                    "assetType": "constructor",
                    "displayName": "CSV Constructor One",
                    "priceMillions": "18",
                    "ownershipPct": "22.0",
                    "unknownColumn": "ignored",
                },
            ],
            [
                "assetId",
                "assetType",
                "displayName",
                "priceMillions",
                "ownershipPct",
                "unknownColumn",
            ],
        ),
    }

    response = client.post("/api/v1/fantasy/import/market", json=good)

    assert response.status_code == 201
    body = response.json()
    assert body["itemCount"] == 2
    assert any("unknownColumn" in warning for warning in body["warnings"])
    assets = client.get("/api/v1/fantasy/assets", params={"eventId": "event_csv"}).json()["items"]
    assert {asset["assetId"] for asset in assets} == {"csv_driver_one", "csv_constructor_one"}


def test_league_csv_import_feeds_analysis() -> None:
    payload = {
        "format": "csv",
        "leagueId": "league_csv",
        "eventId": "event_demo_01",
        "content": _csv(
            [
                {
                    "teamName": "CSV Rival",
                    "points": "1200",
                    "assetIds": "asset_driver_alpha;asset_constructor_two",
                }
            ],
            ["teamName", "points", "assetIds"],
        ),
    }

    response = client.post("/api/v1/leagues/import", json=payload)

    assert response.status_code == 201
    assert response.json()["itemCount"] == 1
    analysis = client.get("/api/v1/leagues/league_csv/analysis").json()
    assert analysis["leagueId"] == "league_csv"
    assert "asset_driver_alpha" in analysis["commonAssetIds"]


def _csv(rows: list[dict[str, str]], fieldnames: list[str]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
