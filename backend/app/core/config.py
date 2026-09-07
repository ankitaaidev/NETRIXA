"""
Centralized application configuration.

All settings are sourced from environment variables (see .env.example).
Never hard-code secrets here. DEMO_MODE must allow the entire application
to function with no database, no FIRMS key, and no internet access.
"""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Core ---
    APP_NAME: str = "NETRIXA"
    ENVIRONMENT: str = "development"
    DEMO_MODE: bool = True

    # --- Database ---
    # Left unset (None) in demo mode is expected and handled gracefully.
    DATABASE_URL: str | None = Field(default=None)

    # --- CORS ---
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: [
        "http://localhost:5173",
        "http://localhost:8443",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8443",
    ])

    # --- FIRMS (NASA) ---
    FIRMS_API_KEY: str | None = Field(default=None)

    # --- Risk thresholds (kept configurable per Phase 8 / Settings page) ---
    RISK_LOW_MAX: int = 25
    RISK_MEDIUM_MAX: int = 50
    RISK_HIGH_MAX: int = 75  # anything above this is CRITICAL

    # In demo mode, "now" is pinned to this date so activity windows (last
    # 30/90 days) stay stable regardless of real wall-clock time — the
    # demo dataset is generated relative to this same anchor (see
    # app.database.seed.DEMO_TODAY, which must match).
    DEMO_ANCHOR_DATE: str = "2026-09-04"


@lru_cache
def get_settings() -> Settings:
    return Settings()
