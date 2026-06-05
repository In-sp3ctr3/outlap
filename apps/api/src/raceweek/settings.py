from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RACEWEEK_", env_file=".env", extra="ignore")

    database_path: str = "./data/raceweek.duckdb"
    demo_mode: bool = True


settings = Settings()
