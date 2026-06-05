from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from raceweek.main import app

client = TestClient(app)
ALLOWED_STATUSES = {"ok", "stale", "degraded", "error", "disabled", "unknown"}


@pytest.fixture(autouse=True)
def reset_demo_state() -> None:
    client.post("/api/v1/demo/reset")


def test_data_source_statuses_match_public_contract() -> None:
    statuses = client.get("/api/v1/data-sources/status").json()["items"]

    assert statuses
    assert {status["status"] for status in statuses} <= ALLOWED_STATUSES
    assert all(status["status"] != "healthy" for status in statuses)
