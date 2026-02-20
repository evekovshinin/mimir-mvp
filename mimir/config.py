"""Configuration module for Mimir."""
import logging
import os
from pathlib import Path

try:
    from pydantic_settings import BaseSettings
except Exception:
    # Lightweight fallback for test environments where pydantic_settings
    # is not available. This allows tests to import `mimir.config` without
    # installing dependencies. The fallback does not provide env-var
    # parsing; it only allows `Settings()` to be instantiated.
    class BaseSettings:  # type: ignore
        class Config:  # placeholder
            env_file = ".env"
            case_sensitive = False


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/mimir"
    database_echo: bool = False

    # Application
    app_name: str = "mimir"
    debug: bool = False

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()


def setup_logging() -> logging.Logger:
    """Configure logging for the application."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    return logging.getLogger(settings.app_name)


logger = setup_logging()

# Mimir local state directory
MIMIR_DIR = Path.home() / ".mimir"
MIMIR_DIR.mkdir(exist_ok=True)
STATE_FILE = MIMIR_DIR / "state.json"
