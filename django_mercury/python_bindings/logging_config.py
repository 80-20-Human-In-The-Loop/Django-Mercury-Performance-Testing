"""Logging configuration for the Performance Testing Framework

This module provides centralized logging configuration for all components
of the performance testing framework.
"""

import logging
import logging.config
import os
from pathlib import Path
from typing import Dict, Any

# Default log format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DETAILED_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s"


def get_log_level() -> str:
    """Get log level from environment variable or default to INFO."""
    return os.environ.get("MERCURY_LOG_LEVEL", "INFO").upper()


def get_log_config() -> Dict[str, Any]:
    """Get logging configuration dictionary."""
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {"format": DEFAULT_LOG_FORMAT, "datefmt": "%Y-%m-%d %H:%M:%S"},
            "detailed": {"format": DETAILED_LOG_FORMAT, "datefmt": "%Y-%m-%d %H:%M:%S"},
            "colored": {
                "()": "colorlog.ColoredFormatter",
                "format": "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(name)s%(reset)s - %(message)s",
                "log_colors": {
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red,bg_white",
                },
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "colored" if _has_colorlog() else "default",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": str(log_dir / "performance_testing.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": str(log_dir / "performance_testing_errors.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "performance_testing": {
                "handlers": ["console", "file", "error_file"],
                "level": get_log_level(),
                "propagate": False,
            },
            "performance_testing.monitor": {
                "handlers": ["console", "file"],
                "level": get_log_level(),
                "propagate": False,
            },
            "performance_testing.mercury": {
                "handlers": ["console", "file"],
                "level": get_log_level(),
                "propagate": False,
            },
            "performance_testing.django_hooks": {
                "handlers": ["console", "file"],
                "level": get_log_level(),
                "propagate": False,
            },
        },
        "root": {"level": "INFO", "handlers": ["console"]},
    }


def _has_colorlog() -> bool:
    """Check if colorlog is available."""
    try:
        import colorlog

        return True
    except ImportError:
        return False


def setup_logging():
    """Set up logging configuration for the performance testing framework."""
    config = get_log_config()

    # Only configure if not already configured
    if not logging.getLogger("performance_testing").handlers:
        logging.config.dictConfig(config)

        # Log startup message
        logger = logging.getLogger("performance_testing")
        logger.info("Performance Testing Framework logging initialized")
        logger.debug(f"Log level set to: {get_log_level()}")


# Create module-level loggers
def get_logger(name: str) -> logging.Logger:
    """Get a logger for the specified module name.

    Args:
        name: The name of the module requesting the logger.

    Returns:
        logging.Logger: Configured logger instance.
    """
    # Ensure logging is set up
    setup_logging()

    # Convert None or non-string names to string
    if name is None:
        name = "None"
    else:
        name = str(name)

    # Prefix with our namespace if not already
    if not name.startswith("performance_testing"):
        name = f"performance_testing.{name}"

    return logging.getLogger(name)


# Initialize logging on import
setup_logging()
