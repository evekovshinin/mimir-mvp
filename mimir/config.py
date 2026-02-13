"""Configuration module for Mimir."""
import logging
import os
from pathlib import Path

from pydantic_settings import BaseSettings


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
