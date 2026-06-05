from __future__ import annotations

from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RACEWEEK_", env_file=".env", extra="ignore")

    database_path: str = str(REPO_ROOT / "data" / "raceweek.duckdb")
    demo_mode: bool = True
    fantasy_api_base_url: str = Field(
        default="https://fantasy-api.formula1.com/partner_games/f1",
        validation_alias=AliasChoices("RACEWEEK_FANTASY_API_BASE_URL", "FANTASY_API_BASE_URL"),
    )
    fantasy_game_version: str = Field(
        default="2022",
        validation_alias=AliasChoices("RACEWEEK_FANTASY_GAME_VERSION", "FANTASY_GAME_VERSION"),
    )
    fantasy_session_token: str | None = Field(
        default=None,
        validation_alias=AliasChoices("RACEWEEK_FANTASY_SESSION_TOKEN", "FANTASY_SESSION_TOKEN"),
    )


settings = Settings()
