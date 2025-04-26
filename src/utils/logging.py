"""Logging utilities for the application.

This module provides functions to configure logging and
retrieve configured logger instances.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional, Union, List


def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> None:
    """Configure application-wide logging.

    Args:
        log_level: The logging level to use
        log_file: Optional path to a log file
        log_format: The format string for log messages
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
    """
    handlers: List[logging.Handler] = []

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)

    # Create file handler if log_file is specified
    if log_file:
        try:
            # Ensure the directory exists
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            # Create rotating file handler
            file_handler = RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count
            )
            file_handler.setFormatter(logging.Formatter(log_format))
            handlers.append(file_handler)
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not set up file logging: {str(e)}")

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add our handlers
    for handler in handlers:
        root_logger.addHandler(handler)


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """Get a configured logger with the given name.

    Args:
        name: The name for the logger instance
        level: Optional specific level for this logger

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)

    # Set specific level if provided
    if level is not None:
        logger.setLevel(level)

    return logger
