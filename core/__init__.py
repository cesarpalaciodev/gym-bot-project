"""Core package with logging, errors, and error handling."""

from __future__ import annotations

from core.error_handler import (
    ErrorHandler,
    get_error_handler,
    safe_execute,
    safe_execute_async,
)
from core.errors import (
    AppError,
    AuthError,
    BusinessError,
    ConfigurationError,
    DatabaseError,
    DuplicateError,
    ExternalServiceError,
    FieldValidationError,
    ForbiddenError,
    NotFoundError,
    RequiredFieldError,
    SystemError,
    TelegramAPIError,
    UnauthorizedError,
    ValidationError,
    convert_exception,
    is_system_error,
    is_user_error,
)
from core.logging import (
    ContextAdapter,
    get_logger,
    log_execution_time,
    setup_logging,
)

__all__ = [
    # Logging
    "setup_logging",
    "get_logger",
    "ContextAdapter",
    "log_execution_time",
    # Errors
    "AppError",
    "ValidationError",
    "FieldValidationError",
    "RequiredFieldError",
    "NotFoundError",
    "DuplicateError",
    "AuthError",
    "UnauthorizedError",
    "ForbiddenError",
    "BusinessError",
    "ExternalServiceError",
    "DatabaseError",
    "TelegramAPIError",
    "SystemError",
    "ConfigurationError",
    # Error utilities
    "convert_exception",
    "is_user_error",
    "is_system_error",
    # Error handling
    "ErrorHandler",
    "get_error_handler",
    "safe_execute",
    "safe_execute_async",
]
