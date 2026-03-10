"""Centralized logger setup to decouple logging from handlers."""
import logging

from mimir.config import settings


def setup_logger(name: str | None = None) -> logging.Logger:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name or settings.app_name)
    logger.setLevel(level)
    # avoid duplicate handlers if already configured
    if not logger.handlers:
        logger.addHandler(handler)

    return logger


logger = setup_logger()
