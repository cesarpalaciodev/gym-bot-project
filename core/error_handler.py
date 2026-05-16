"""Centralized error handling for the application."""

from __future__ import annotations

import functools
import logging
from typing import Any, Callable, TypeVar

from telegram import Update
from telegram.ext import ContextTypes

from core.errors import AppError, convert_exception
from core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class ErrorHandler:
    """Centralized error handler for the application.

    Provides:
    - Consistent error logging
    - User-friendly error messages
    - Error tracking and metrics
    - Graceful degradation
    """

    def __init__(self) -> None:
        self._error_counts: dict[str, int] = {}

    def handle_error(
        self,
        error: Exception,
        context: dict[str, Any] | None = None,
    ) -> AppError:
        """Process and log error.

        Args:
            error: Original exception
            context: Error context (user_id, operation, etc.)

        Returns:
            Structured AppError
        """
        # Convert to AppError
        if not isinstance(error, AppError):
            app_error = convert_exception(error)
        else:
            app_error = error

        # Add context if provided
        if context:
            app_error = app_error.with_context(**context)

        # Capture traceback if not already captured
        if not app_error.traceback:
            app_error.capture_traceback()

        # Track error
        self._error_counts[app_error.code] = self._error_counts.get(app_error.code, 0) + 1

        # Log based on severity
        self._log_error(app_error)

        return app_error

    def _log_error(self, error: AppError) -> None:
        """Log error with appropriate level.

        Args:
            error: Error to log
        """
        extra = {
            "error_code": error.code,
            "error_details": error.details,
            "error_context": error.context,
        }

        if error.http_status >= 500:
            # System error - CRITICAL
            logger.critical(
                f"System error [{error.code}]: {error.args[0]}",
                extra=extra,
                exc_info=bool(error.cause),
            )
        elif error.http_status == 403:
            # Forbidden - WARNING
            logger.warning(
                f"Access denied [{error.code}]: {error.args[0]}",
                extra=extra,
            )
        elif error.http_status == 404:
            # Not found - INFO (common)
            logger.info(
                f"Resource not found [{error.code}]: {error.args[0]}",
                extra=extra,
            )
        elif error.http_status >= 400:
            # User error - WARNING
            logger.warning(
                f"User error [{error.code}]: {error.args[0]}",
                extra=extra,
            )
        else:
            # Unknown - ERROR
            logger.error(
                f"Application error [{error.code}]: {error.args[0]}",
                extra=extra,
                exc_info=True,
            )

    async def handle_telegram_error(
        self,
        update: Update | None,
        context: ContextTypes.DEFAULT_TYPE,
        error: Exception,
    ) -> None:
        """Handle errors in Telegram handlers.

        Args:
            update: Telegram update
            context: Handler context
            error: Exception that occurred
        """
        # Build context
        error_context: dict[str, Any] = {
            "handler": context.error.__class__.__name__ if context.error else "unknown",
        }

        if update and update.effective_user:
            error_context["user_id"] = update.effective_user.id

        if update and update.effective_chat:
            error_context["chat_id"] = update.effective_chat.id

        # Process error
        app_error = self.handle_error(error, error_context)

        # Send user-friendly message
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(f"❌ {app_error.user_message}\n\nCódigo: {app_error.code}")
            except Exception as e:
                logger.error(f"Failed to send error message: {e}")

    def get_error_stats(self) -> dict[str, int]:
        """Get error statistics.

        Returns:
            Error counts by code
        """
        return self._error_counts.copy()

    def reset_stats(self) -> None:
        """Reset error statistics."""
        self._error_counts.clear()


# Global error handler instance
_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """Get global error handler instance.

    Returns:
        ErrorHandler singleton
    """
    return _error_handler


def safe_execute(
    default_return: T | None = None,
    log_errors: bool = True,
    reraise: bool = False,
) -> Callable:
    """Decorator to safely execute function with error handling.

    Args:
        default_return: Value to return on error
        log_errors: Whether to log errors
        reraise: Whether to re-raise exception

    Returns:
        Decorator function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T | None]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T | None:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    handler = get_error_handler()
                    handler.handle_error(
                        e,
                        context={"function": func.__name__},
                    )

                if reraise:
                    raise

                return default_return

        return wrapper

    return decorator


async def safe_execute_async(
    func: Callable[..., T],
    *args: Any,
    default_return: T | None = None,
    error_context: dict[str, Any] | None = None,
    **kwargs: Any,
) -> T | None:
    """Safely execute async function with error handling.

    Args:
        func: Function to execute
        *args: Function arguments
        default_return: Value to return on error
        error_context: Error context
        **kwargs: Function keyword arguments

    Returns:
        Function result or default_return on error
    """
    try:
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    except Exception as e:
        handler = get_error_handler()
        context = error_context or {}
        context["function"] = func.__name__
        handler.handle_error(e, context)
        return default_return


# Import here to avoid circular imports
import asyncio
