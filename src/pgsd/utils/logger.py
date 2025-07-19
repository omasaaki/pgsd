"""Logging utilities for PGSD."""

import structlog
import sys
import logging
import logging.handlers
from typing import Any, Dict, Optional
from .log_config import LogConfig, get_default_config


class PGSDLogger:
    """Unified logger interface for PGSD."""

    def __init__(self, name: str) -> None:
        """Initialize logger with given name.

        Args:
            name: Logger name (typically module name)
        """
        self.name = name
        self._logger = structlog.get_logger(name)

    def debug(self, event: str, **kwargs: Any) -> None:
        """Log debug message with structured data.

        Args:
            event: Event description
            **kwargs: Additional structured data
        """
        self._logger.debug(event, **self._sanitize_data(kwargs))

    def info(self, event: str, **kwargs: Any) -> None:
        """Log info message with structured data.

        Args:
            event: Event description
            **kwargs: Additional structured data
        """
        self._logger.info(event, **self._sanitize_data(kwargs))

    def warning(self, event: str, **kwargs: Any) -> None:
        """Log warning message with structured data.

        Args:
            event: Event description
            **kwargs: Additional structured data
        """
        self._logger.warning(event, **self._sanitize_data(kwargs))

    def error(self, event: str, **kwargs: Any) -> None:
        """Log error message with structured data.

        Args:
            event: Event description
            **kwargs: Additional structured data
        """
        self._logger.error(event, **self._sanitize_data(kwargs))

    def critical(self, event: str, **kwargs: Any) -> None:
        """Log critical message with structured data.

        Args:
            event: Event description
            **kwargs: Additional structured data
        """
        self._logger.critical(event, **self._sanitize_data(kwargs))

    def exception(self, event: str, **kwargs: Any) -> None:
        """Log exception with traceback.

        Args:
            event: Event description
            **kwargs: Additional structured data
        """
        self._logger.exception(event, **self._sanitize_data(kwargs))

    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from log data.

        Args:
            data: Original data dictionary

        Returns:
            Sanitized data dictionary
        """
        SENSITIVE_FIELDS = {
            "password",
            "secret",
            "token",
            "key",
            "credential",
            "auth",
            "private",
            "passwd",
        }

        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in SENSITIVE_FIELDS):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            else:
                sanitized[key] = value

        return sanitized


# Global logger registry
_logger_registry: Dict[str, PGSDLogger] = {}
_is_configured = False


def get_logger(name: str) -> PGSDLogger:
    """Get logger instance for the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        PGSDLogger instance
    """
    if not _is_configured:
        setup_logging()

    if name not in _logger_registry:
        _logger_registry[name] = PGSDLogger(name)

    return _logger_registry[name]


def setup_logging(config: Optional[LogConfig] = None) -> None:
    """Setup structlog configuration.

    Args:
        config: Logging configuration. If None, uses default config.
    """
    global _is_configured

    if config is None:
        config = get_default_config()

    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
    ]

    if config.format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Define formatters
    if config.format == "json":
        # JSON format already handled by structlog processors
        formatter = None
    else:
        # Console format with date/time and log level
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # Console handler
    if config.console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, config.level.upper()))
        if formatter:
            console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler with rotation
    if config.file_path:
        config.file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            config.file_path,
            maxBytes=config.max_file_size,
            backupCount=config.backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(getattr(logging, config.level.upper()))
        if formatter:
            file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    _is_configured = True


def reset_logging() -> None:
    """Reset logging configuration (primarily for testing)."""
    global _is_configured
    _is_configured = False
    _logger_registry.clear()

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
