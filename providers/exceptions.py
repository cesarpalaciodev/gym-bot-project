"""Exceptions for external API providers."""

from __future__ import annotations


class ProviderError(Exception):
    """Base exception for all provider errors."""

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        error_code: str | None = None,
        original_error: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.error_code = error_code
        self.original_error = original_error

    def __str__(self) -> str:
        parts = [self.args[0]]
        if self.provider:
            parts.append(f"provider={self.provider}")
        if self.error_code:
            parts.append(f"code={self.error_code}")
        return " | ".join(parts)


class ProviderConnectionError(ProviderError):
    """Could not connect to external service."""

    pass


class ProviderTimeoutError(ProviderError):
    """External service timeout."""

    pass


class ProviderRateLimitError(ProviderError):
    """Rate limit exceeded for external service."""

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        retry_after: int | None = None,
        error_code: str | None = None,
        original_error: Exception | None = None,
    ) -> None:
        super().__init__(message, provider, error_code, original_error)
        self.retry_after = retry_after


class ProviderAuthenticationError(ProviderError):
    """Authentication failed with external service."""

    pass


class ProviderNotFoundError(ProviderError):
    """Resource not found in external service."""

    pass


class ProviderValidationError(ProviderError):
    """Invalid data sent to external service."""

    pass


class ProviderServerError(ProviderError):
    """External service server error (5xx)."""

    pass


# Error code mapping for common scenarios
ERROR_CODES = {
    "CONNECTION_REFUSED": "provider_connection_refused",
    "TIMEOUT": "provider_timeout",
    "RATE_LIMIT": "provider_rate_limited",
    "AUTH_FAILED": "provider_auth_failed",
    "NOT_FOUND": "provider_not_found",
    "VALIDATION": "provider_validation_error",
    "SERVER_ERROR": "provider_server_error",
    "UNKNOWN": "provider_unknown_error",
}
