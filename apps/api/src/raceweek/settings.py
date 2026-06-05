from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RACEWEEK_", env_file=".env", extra="ignore")

    database_path: str = str(REPO_ROOT / "data" / "raceweek.duckdb")
    demo_mode: bool = True


settings = Settings()
