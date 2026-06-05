from __future__ import annotations

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
