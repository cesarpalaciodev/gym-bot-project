"""Standardized response format for all providers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class ProviderResponse(Generic[T]):
    """Standardized response wrapper for all provider operations.

    This ensures all external API calls return a consistent format,
    making error handling and response processing predictable.

    Attributes:
        data: The actual response data (None if error)
        success: Whether the operation succeeded
        provider: Identifier of the provider that made the call
        error_message: Human-readable error description
        error_code: Machine-readable error code for categorization
        metadata: Additional context (timing, rate limits, etc.)
    """

    data: T | None
    success: bool
    provider: str
    error_message: str | None = None
    error_code: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_error(self) -> bool:
        """Check if response indicates an error."""
        return not self.success

    @property
    def is_success(self) -> bool:
        """Check if response indicates success."""
        return self.success

    def get_data(self) -> T:
        """Get data or raise exception if error.

        Raises:
            ValueError: If response is an error.

        Returns:
            The response data.
        """
        if self.is_error or self.data is None:
            raise ValueError(f"Cannot get data from error response: {self.error_message}")
        return self.data

    def get_or_default(self, default: T) -> T:
        """Get data or return default if error.

        Args:
            default: Value to return if error

        Returns:
            Data or default.
        """
        return self.data if self.is_success and self.data is not None else default

    def map(self, fn: callable) -> "ProviderResponse[Any]":
        """Transform response data if successful.

        Args:
            fn: Function to apply to data

        Returns:
            New ProviderResponse with transformed data or same error.
        """
        if self.is_error:
            return ProviderResponse(
                data=None,
                success=False,
                provider=self.provider,
                error_message=self.error_message,
                error_code=self.error_code,
                metadata=self.metadata,
            )

        try:
            new_data = fn(self.data)
            return ProviderResponse(
                data=new_data,
                success=True,
                provider=self.provider,
                metadata=self.metadata,
            )
        except Exception as e:
            return ProviderResponse(
                data=None,
                success=False,
                provider=self.provider,
                error_message=f"Transform error: {e}",
                error_code="TRANSFORM_ERROR",
                metadata=self.metadata,
            )


def success_response(
    data: T,
    provider: str,
    metadata: dict[str, Any] | None = None,
) -> ProviderResponse[T]:
    """Create a success response.

    Args:
        data: Response data
        provider: Provider name
        metadata: Optional metadata

    Returns:
        Success ProviderResponse
    """
    return ProviderResponse(
        data=data,
        success=True,
        provider=provider,
        metadata=metadata or {},
    )


def error_response(
    error_message: str,
    provider: str,
    error_code: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> ProviderResponse[Any]:
    """Create an error response.

    Args:
        error_message: Error description
        provider: Provider name
        error_code: Error code
        metadata: Optional metadata

    Returns:
        Error ProviderResponse
    """
    return ProviderResponse(
        data=None,
        success=False,
        provider=provider,
        error_message=error_message,
        error_code=error_code or "UNKNOWN_ERROR",
        metadata=metadata or {},
    )
