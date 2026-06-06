from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from raceweek.settings import Settings


def test_fantasy_settings_accept_spec_env_names(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FANTASY_API_BASE_URL", "https://fantasy-api.example.test/f1")
    monkeypatch.setenv("FANTASY_GAME_VERSION", "2099")
    monkeypatch.setenv("FANTASY_SESSION_TOKEN", "token-value")

    settings = Settings()

    assert settings.fantasy_api_base_url == "https://fantasy-api.example.test/f1"
    assert settings.fantasy_game_version == "2099"
    assert settings.fantasy_session_token == "token-value"


def test_fantasy_game_version_defaults_to_current_utc_year(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RACEWEEK_FANTASY_GAME_VERSION", raising=False)
    monkeypatch.delenv("FANTASY_GAME_VERSION", raising=False)

    settings = Settings(_env_file=None)

    assert settings.fantasy_game_version == str(datetime.now(UTC).year)
    assert settings.fantasy_game_version != "2022"


def test_blank_fantasy_game_version_uses_current_utc_year(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RACEWEEK_FANTASY_GAME_VERSION", raising=False)
    monkeypatch.setenv("FANTASY_GAME_VERSION", "")

    settings = Settings(_env_file=None)

    assert settings.fantasy_game_version == str(datetime.now(UTC).year)


def test_env_examples_do_not_pin_stale_fantasy_game_version() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    for relative_path in [".env.example", "examples/.env.example"]:
        contents = (repo_root / relative_path).read_text()

        assert "FANTASY_GAME_VERSION=2022" not in contents
        assert "RACEWEEK_FANTASY_GAME_VERSION=2022" not in contents


def test_database_path_accepts_rws_env_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RWS_DUCKDB_PATH", "/tmp/outlap-test.duckdb")

    settings = Settings()

    assert settings.database_path == "/tmp/outlap-test.duckdb"
