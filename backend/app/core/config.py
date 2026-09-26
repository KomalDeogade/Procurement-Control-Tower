"""
Application configuration loaded from environment variables.

All secrets come from .env / environment — never hard-coded.
"""

from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central settings read from environment / .env file."""

    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./scm_procurement.db"

    # ── Authentication ───────────────────────────────────
    JWT_SECRET: str = "change-this-to-a-secure-random-string-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 480

    # ── Mock SAP ─────────────────────────────────────────
    MOCK_SAP_URL: str = "http://localhost:8001"

    # ── AI (future – provider-agnostic interface) ────────
    AI_PROVIDER: str = "none"
    AI_API_KEY: Optional[str] = None
    AI_MODEL: Optional[str] = None

    # ── Application ──────────────────────────────────────
    APP_NAME: str = "SCM Procurement Control Tower"
    APP_ENV: str = "development"

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
    }


settings = Settings()
