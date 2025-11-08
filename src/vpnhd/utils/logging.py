"""Logging configuration for VPNHD."""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler

from .constants import LOG_DIR, LOG_FILE, APP_NAME


def setup_logging(
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    verbose: bool = False,
) -> None:
    """
    Set up logging configuration for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console
        verbose: Enable verbose logging (DEBUG level)
    """
    # Determine log level
    if verbose:
        level = logging.DEBUG
    else:
        level = getattr(logging, log_level.upper(), logging.INFO)

    # Create logger
    logger = logging.getLogger(APP_NAME)
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    simple_formatter = logging.Formatter(fmt="%(levelname)s: %(message)s")

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_to_file:
        try:
            # Ensure log directory exists
            LOG_DIR.mkdir(parents=True, exist_ok=True)

            # Create rotating file handler (max 10MB, keep 5 backups)
            file_handler = RotatingFileHandler(
                LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 10 MB
            )
            file_handler.setLevel(logging.DEBUG)  # Always log everything to file
            file_handler.setFormatter(detailed_formatter)
            logger.addHandler(file_handler)

        except Exception as e:
            # If we can't create log file, just log to console
            logger.warning(f"Could not create log file: {e}")

    # Prevent propagation to root logger
    logger.propagate = False


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (default: APP_NAME)

    Returns:
        logging.Logger: Logger instance
    """
    if name:
        return logging.getLogger(f"{APP_NAME}.{name}")
    return logging.getLogger(APP_NAME)


class LoggerMixin:
    """Mixin class to add logging capability to any class."""

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        return get_logger(self.__class__.__name__)


def log_function_call(func):
    """
    Decorator to log function calls.

    Args:
        func: Function to decorate

    Returns:
        Wrapped function
    """

    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} returned {result}")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} raised {type(e).__name__}: {e}")
            raise

    return wrapper


def log_exceptions(func):
    """
    Decorator to log exceptions.

    Args:
        func: Function to decorate

    Returns:
        Wrapped function
    """

    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Exception in {func.__name__}: {e}")
            raise

    return wrapper
