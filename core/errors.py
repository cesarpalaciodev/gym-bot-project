"""Application error hierarchy with structured error information."""

from __future__ import annotations

import traceback
from typing import Any


class AppError(Exception):
    """Base exception for all application errors.

    Provides structured error information including:
    - Error code for programmatic handling
    - HTTP status code for API responses
    - User-friendly message
    - Internal details for debugging
    - Error context (request ID, user ID, etc.)
    """

    # Default error properties
    code: str = "INTERNAL_ERROR"
    http_status: int = 500
    user_message: str = "An unexpected error occurred"

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        http_status: int | None = None,
        user_message: str | None = None,
        details: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        """Initialize application error.

        Args:
            message: Technical error message
            code: Error code for categorization
            http_status: HTTP status code for API
            user_message: User-friendly error message
            details: Additional error details
            context: Request context (user_id, request_id, etc.)
            cause: Original exception that caused this error
        """
        super().__init__(message or self.user_message)

        self.code = code or self.code
        self.http_status = http_status or self.http_status
        self.user_message = user_message or self.user_message
        self.details = details or {}
        self.context = context or {}
        self.cause = cause
        self.traceback: list[str] = []

    def __str__(self) -> str:
        """String representation with error code."""
        return f"[{self.code}] {self.args[0]}"

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"{self.__class__.__name__}(code={self.code!r}, message={self.args[0]!r}, http_status={self.http_status})"
        )

    def to_dict(self, include_traceback: bool = False) -> dict[str, Any]:
        """Convert error to dictionary for serialization.

        Args:
            include_traceback: Include stack trace

        Returns:
            Error dictionary
        """
        result = {
            "error": {
                "code": self.code,
                "message": self.user_message,
                "details": self.details,
            }
        }

        if self.context:
            result["context"] = self.context

        if include_traceback and self.traceback:
            result["traceback"] = self.traceback

        return result

    def with_context(self, **kwargs: Any) -> "AppError":
        """Create copy with additional context.

        Args:
            **kwargs: Context key-value pairs

        Returns:
            New error with merged context
        """
        new_context = {**self.context, **kwargs}
        new_error = self.__class__(
            message=self.args[0],
            code=self.code,
            http_status=self.http_status,
            user_message=self.user_message,
            details=self.details.copy(),
            context=new_context,
            cause=self.cause,
        )
        new_error.traceback = self.traceback.copy()
        return new_error

    def capture_traceback(self) -> "AppError":
        """Capture current stack trace.

        Returns:
            Self for chaining
        """
        self.traceback = traceback.format_exc().splitlines()
        return self


# Validation Errors


class ValidationError(AppError):
    """Invalid input data."""

    code = "VALIDATION_ERROR"
    http_status = 400
    user_message = "Invalid input data"


class FieldValidationError(ValidationError):
    """Specific field validation error."""

    code = "FIELD_VALIDATION_ERROR"

    def __init__(
        self,
        field: str,
        message: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message=f"Field '{field}': {message}",
            details={"field": field, "error": message},
            **kwargs,
        )


class RequiredFieldError(ValidationError):
    """Missing required field."""

    code = "REQUIRED_FIELD"
    user_message = "Required field is missing"

    def __init__(self, field: str, **kwargs: Any) -> None:
        super().__init__(
            message=f"Required field '{field}' is missing",
            details={"field": field},
            **kwargs,
        )


# Resource Errors


class ResourceError(AppError):
    """Base for resource-related errors."""

    pass


class NotFoundError(ResourceError):
    """Resource not found."""

    code = "NOT_FOUND"
    http_status = 404
    user_message = "Resource not found"

    def __init__(
        self,
        resource_type: str,
        resource_id: str | int | None = None,
        **kwargs: Any,
    ) -> None:
        message = f"{resource_type} not found"
        if resource_id:
            message = f"{resource_type} with id={resource_id} not found"

        super().__init__(
            message=message,
            details={"resource_type": resource_type, "resource_id": resource_id},
            **kwargs,
        )


class DuplicateError(ResourceError):
    """Resource already exists."""

    code = "DUPLICATE_ERROR"
    http_status = 409
    user_message = "Resource already exists"

    def __init__(
        self,
        resource_type: str,
        identifier: str | None = None,
        **kwargs: Any,
    ) -> None:
        message = f"{resource_type} already exists"
        if identifier:
            message = f"{resource_type} with identifier '{identifier}' already exists"

        super().__init__(
            message=message,
            details={"resource_type": resource_type, "identifier": identifier},
            **kwargs,
        )


# Authentication/Authorization Errors


class AuthError(AppError):
    """Base for authentication errors."""

    code = "AUTH_ERROR"
    http_status = 401
    user_message = "Authentication failed"


class UnauthorizedError(AuthError):
    """Not authenticated."""

    code = "UNAUTHORIZED"
    http_status = 401
    user_message = "Authentication required"


class ForbiddenError(AppError):
    """Not authorized for operation."""

    code = "FORBIDDEN"
    http_status = 403
    user_message = "You don't have permission to perform this action"


# Business Logic Errors


class BusinessError(AppError):
    """Business rule violation."""

    code = "BUSINESS_ERROR"
    http_status = 422
    user_message = "Operation cannot be completed"


class StateError(BusinessError):
    """Invalid state for operation."""

    code = "INVALID_STATE"
    user_message = "Invalid state for this operation"


# External Service Errors


class ExternalServiceError(AppError):
    """External service failure."""

    code = "EXTERNAL_SERVICE_ERROR"
    http_status = 502
    user_message = "External service unavailable"


class DatabaseError(ExternalServiceError):
    """Database operation failed."""

    code = "DATABASE_ERROR"
    http_status = 500
    user_message = "Database operation failed"


class TelegramAPIError(ExternalServiceError):
    """Telegram API error."""

    code = "TELEGRAM_API_ERROR"
    http_status = 502
    user_message = "Telegram service unavailable"


# System Errors


class SystemError(AppError):
    """Internal system error."""

    code = "SYSTEM_ERROR"
    http_status = 500
    user_message = "Internal system error"


class ConfigurationError(SystemError):
    """Invalid configuration."""

    code = "CONFIGURATION_ERROR"
    http_status = 500
    user_message = "System configuration error"


# Error utilities


def convert_exception(exc: Exception) -> AppError:
    """Convert standard exception to AppError.

    Args:
        exc: Original exception

    Returns:
        AppError wrapper
    """
    if isinstance(exc, AppError):
        return exc

    # Map common exceptions
    mapping = {
        ValueError: (ValidationError, "Invalid value provided"),
        TypeError: (ValidationError, "Invalid type provided"),
        KeyError: (NotFoundError, "Required key not found"),
        FileNotFoundError: (NotFoundError, "File not found"),
        PermissionError: (ForbiddenError, "Permission denied"),
    }

    error_class, default_message = mapping.get(type(exc), (SystemError, str(exc)))

    return error_class(
        message=str(exc) or default_message,
        cause=exc,
    ).capture_traceback()


def is_user_error(error: AppError) -> bool:
    """Check if error is caused by user input (4xx).

    Args:
        error: Error to check

    Returns:
        True if 4xx error
    """
    return 400 <= error.http_status < 500


def is_system_error(error: AppError) -> bool:
    """Check if error is system error (5xx).

    Args:
        error: Error to check

    Returns:
        True if 5xx error
    """
    return error.http_status >= 500
