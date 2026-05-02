"""Logging utilities for NepSense."""

import logging
from pathlib import Path

from nepsense.config import LOG_FORMAT, LOG_LEVEL


def setup_logger(name: str, log_file: Path | None = None) -> logging.Logger:
    """Set up a logger with console and optional file handlers.
    
    Args:
        name: Logger name (usually __name__)
        log_file: Optional path to log file
    
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOG_LEVEL))
    formatter = logging.Formatter(LOG_FORMAT)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if requested
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, LOG_LEVEL))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
