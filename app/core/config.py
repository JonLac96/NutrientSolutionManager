from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NSM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./nsm.db"
    log_level: str = "INFO"
    default_stabilization_seconds: int = 120
    default_max_correction_attempts: int = 3
    default_max_cycle_duration_minutes: int = 1440


@lru_cache
def get_settings() -> Settings:
    return Settings()
