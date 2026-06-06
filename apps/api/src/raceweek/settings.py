from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[4]


def current_utc_year() -> str:
    return str(datetime.now(UTC).year)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RACEWEEK_", env_file=".env", extra="ignore")

    database_path: str = Field(
        default=str(REPO_ROOT / "data" / "raceweek.duckdb"),
        validation_alias=AliasChoices("RWS_DUCKDB_PATH", "RACEWEEK_DATABASE_PATH"),
    )
    demo_mode: bool = False
    fantasy_api_base_url: str = Field(
        default="https://fantasy-api.formula1.com/partner_games/f1",
        validation_alias=AliasChoices("RACEWEEK_FANTASY_API_BASE_URL", "FANTASY_API_BASE_URL"),
    )
    fantasy_game_version: str = Field(
        default_factory=current_utc_year,
        validation_alias=AliasChoices("RACEWEEK_FANTASY_GAME_VERSION", "FANTASY_GAME_VERSION"),
    )
    fantasy_session_token: str | None = Field(
        default=None,
        validation_alias=AliasChoices("RACEWEEK_FANTASY_SESSION_TOKEN", "FANTASY_SESSION_TOKEN"),
    )
    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("RACEWEEK_OPENAI_API_KEY", "OPENAI_API_KEY"),
    )
    anthropic_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("RACEWEEK_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY"),
    )
    gemini_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("RACEWEEK_GEMINI_API_KEY", "GEMINI_API_KEY"),
    )
    mistral_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("RACEWEEK_MISTRAL_API_KEY", "MISTRAL_API_KEY"),
    )
    openrouter_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("RACEWEEK_OPENROUTER_API_KEY", "OPENROUTER_API_KEY"),
    )
    groq_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("RACEWEEK_GROQ_API_KEY", "GROQ_API_KEY"),
    )
    xai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("RACEWEEK_XAI_API_KEY", "XAI_API_KEY"),
    )
    custom_openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("RACEWEEK_CUSTOM_OPENAI_API_KEY", "CUSTOM_OPENAI_API_KEY"),
    )
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        validation_alias=AliasChoices("RACEWEEK_OPENAI_BASE_URL", "OPENAI_BASE_URL"),
    )
    mistral_base_url: str = Field(
        default="https://api.mistral.ai/v1",
        validation_alias=AliasChoices("RACEWEEK_MISTRAL_BASE_URL", "MISTRAL_BASE_URL"),
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        validation_alias=AliasChoices("RACEWEEK_OPENROUTER_BASE_URL", "OPENROUTER_BASE_URL"),
    )
    groq_base_url: str = Field(
        default="https://api.groq.com/openai/v1",
        validation_alias=AliasChoices("RACEWEEK_GROQ_BASE_URL", "GROQ_BASE_URL"),
    )
    xai_base_url: str = Field(
        default="https://api.x.ai/v1",
        validation_alias=AliasChoices("RACEWEEK_XAI_BASE_URL", "XAI_BASE_URL"),
    )
    ollama_base_url: str = Field(
        default="http://127.0.0.1:11434",
        validation_alias=AliasChoices("RACEWEEK_OLLAMA_BASE_URL", "OLLAMA_BASE_URL"),
    )
    custom_openai_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("RACEWEEK_CUSTOM_OPENAI_BASE_URL", "CUSTOM_OPENAI_BASE_URL"),
    )
    openai_model: str = Field(
        default="gpt-5.4",
        validation_alias=AliasChoices("RACEWEEK_OPENAI_MODEL", "OPENAI_MODEL"),
    )
    anthropic_model: str = Field(
        default="claude-sonnet-4-5",
        validation_alias=AliasChoices("RACEWEEK_ANTHROPIC_MODEL", "ANTHROPIC_MODEL"),
    )
    gemini_model: str = Field(
        default="gemini-2.5-pro",
        validation_alias=AliasChoices("RACEWEEK_GEMINI_MODEL", "GEMINI_MODEL"),
    )
    ollama_model: str = Field(
        default="llama3.1",
        validation_alias=AliasChoices("RACEWEEK_OLLAMA_MODEL", "OLLAMA_MODEL"),
    )
    mistral_model: str = Field(
        default="mistral-large-latest",
        validation_alias=AliasChoices("RACEWEEK_MISTRAL_MODEL", "MISTRAL_MODEL"),
    )
    openrouter_model: str = Field(
        default="openrouter/auto",
        validation_alias=AliasChoices("RACEWEEK_OPENROUTER_MODEL", "OPENROUTER_MODEL"),
    )
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        validation_alias=AliasChoices("RACEWEEK_GROQ_MODEL", "GROQ_MODEL"),
    )
    xai_model: str = Field(
        default="grok-4",
        validation_alias=AliasChoices("RACEWEEK_XAI_MODEL", "XAI_MODEL"),
    )
    custom_openai_model: str | None = Field(
        default=None,
        validation_alias=AliasChoices("RACEWEEK_CUSTOM_OPENAI_MODEL", "CUSTOM_OPENAI_MODEL"),
    )

    @field_validator("fantasy_game_version", mode="before")
    @classmethod
    def default_blank_fantasy_game_version(cls, value: Any) -> str:
        if value is None:
            return current_utc_year()
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or current_utc_year()
        return str(value)


settings = Settings()
