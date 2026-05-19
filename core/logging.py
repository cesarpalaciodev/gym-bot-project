"""Professional logging configuration with structured output."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "asctime",
            }:
                log_data[key] = value

        return json.dumps(log_data, default=str)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def __init__(self, fmt: str | None = None, use_colors: bool = True) -> None:
        super().__init__(fmt)
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        """Format with colors."""
        if self.use_colors and sys.stdout.isatty():
            color = self.COLORS.get(record.levelname, "")
            record.levelname = f"{color}{record.levelname}{self.RESET}"

        return super().format(record)


def setup_logging(
    level: str = "INFO",
    log_dir: str = "logs",
    app_name: str = "gym-bot",
    json_logs: bool = False,
    console_colors: bool = True,
) -> None:
    """Setup professional logging configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        app_name: Application name for log files
        json_logs: Use JSON format for file logs
        console_colors: Use colored output in console
    """
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    console_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    if console_colors:
        console_formatter: logging.Formatter = ColoredFormatter(console_format)
    else:
        console_formatter = logging.Formatter(console_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler
    timestamp = datetime.now().strftime("%Y-%m-%d")
    log_file = log_path / f"{app_name}-{timestamp}.log"

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)

    if json_logs:
        file_formatter: logging.Formatter = JSONFormatter()
    else:
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(module)s:%(lineno)d | %(message)s"
        )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Error file handler (only ERROR and above)
    error_log_file = log_path / f"{app_name}-error-{timestamp}.log"
    error_handler = logging.FileHandler(error_log_file, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter() if json_logs else file_formatter)
    root_logger.addHandler(error_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)

    logging.info(f"Logging configured. Level: {level}, JSON: {json_logs}")


def get_logger(name: str) -> logging.Logger:
    """Get logger with application context.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger
    """
    return logging.getLogger(name)


class ContextAdapter(logging.LoggerAdapter):  # type: ignore[type-arg]
    """Logger adapter that adds context to all log messages."""

    def __init__(
        self,
        logger: logging.Logger,
        context: dict[str, Any],
    ) -> None:
        super().__init__(logger, context)

    def process(  # type: ignore[override]
        self,
        msg: str,
        kwargs: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """Add context to log record."""
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs


def log_execution_time(
    logger: logging.Logger | None = None,
    level: int = logging.DEBUG,
) -> Any:
    """Decorator to log function execution time.

    Args:
        logger: Logger to use (defaults to root)
        level: Log level for timing message

    Returns:
        Decorator function
    """

    def decorator(func: Any) -> Any:
        import functools
        import time

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            log = logger or logging.getLogger(func.__module__)
            start = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start
                log.log(
                    level,
                    f"{func.__name__} executed in {elapsed:.3f}s",
                    extra={"function": func.__name__, "duration": elapsed},
                )
                return result
            except Exception as e:
                elapsed = time.time() - start
                log.error(
                    f"{func.__name__} failed after {elapsed:.3f}s: {e}",
                    extra={"function": func.__name__, "duration": elapsed, "error": str(e)},
                    exc_info=True,
                )
                raise

        return wrapper

    return decorator


# Global flag to track if logging is configured
_logging_configured = False


def ensure_logging_configured(**kwargs: Any) -> None:
    """Ensure logging is configured, even if called multiple times."""
    global _logging_configured
    if not _logging_configured:
        setup_logging(**kwargs)
        _logging_configured = True
