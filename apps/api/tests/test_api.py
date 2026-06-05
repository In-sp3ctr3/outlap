import pytest
from fastapi.testclient import TestClient

from raceweek.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_demo_state() -> None:
    client.post("/api/v1/demo/reset")


def test_health_and_status() -> None:
    assert client.get("/health").json() == {"status": "ok"}
    status = client.get("/api/v1/app/status").json()
    assert status["setupComplete"] is True
    assert status["databaseReady"] is True


def test_projection_and_recommendation_api() -> None:
    projection = client.post("/api/v1/projections/run", json={"eventId": "event_demo_01"}).json()
    assert projection["projectionRunId"].startswith("projrun_")

    recommendation = client.post(
        "/api/v1/optimizer/recommendations",
        json={
            "teamSnapshotId": "team_demo_01",
            "eventId": "event_demo_01",
            "projectionRunId": projection["projectionRunId"],
            "strategyMode": "balanced",
            "lockedAssetIds": [],
            "bannedAssetIds": [],
            "allowedChips": [],
            "maxOptions": 3,
        },
    ).json()

    assert recommendation["recommendationRunId"].startswith("recrun_")
    assert len(recommendation["options"]) == 3
    assert recommendation["options"][0]["sourceSnapshotIds"]
    assert (
        client.get(f"/api/v1/projections/runs/{projection['projectionRunId']}")
        .json()["projectionRunId"]
        == projection["projectionRunId"]
    )
    assert (
        client.get(f"/api/v1/recommendations/runs/{recommendation['recommendationRunId']}")
        .json()["recommendationRunId"]
        == recommendation["recommendationRunId"]
    )


def test_data_source_failure_degrades_without_breaking_optimizer() -> None:
    failed = client.post("/api/v1/fantasy/sync", json={"simulateFailure": True}).json()
    assert failed["status"] == "degraded"

    statuses = client.get("/api/v1/data-sources/status").json()["items"]
    assert any(item["source"] == "openf1" and item["status"] == "degraded" for item in statuses)

    recommendation = client.post(
        "/api/v1/optimizer/recommendations",
        json={
            "teamSnapshotId": "team_demo_01",
            "eventId": "event_demo_01",
            "strategyMode": "safe",
            "maxOptions": 1,
        },
    ).json()
    assert recommendation["options"][0]["warnings"]


def test_provider_failure_returns_safe_fallback() -> None:
    response = client.post(
        "/api/v1/agent/chat",
        json={
            "conversationId": "conv_test",
            "providerName": "fake-fail",
            "message": "Should I use a chip?",
            "recommendationRunId": None,
        },
    ).json()

    assert response["status"] == "fallback"
    assert "deterministic optimizer" in response["message"]
    assert response["canMutateFantasyAccount"] is False
