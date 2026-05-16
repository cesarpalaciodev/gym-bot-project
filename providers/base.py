"""Base provider interface for external API abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from providers.response import ProviderResponse

T = TypeVar("T")


class BaseProvider(ABC, Generic[T]):
    """Abstract base class for all external API providers.

    Provides common interface for:
    - Response normalization
    - Error handling
    - Retry logic
    - Rate limiting
    """

    def __init__(self, name: str) -> None:
        self._name = name
        self._request_count = 0
        self._error_count = 0

    @property
    def name(self) -> str:
        """Provider identifier."""
        return self._name

    @property
    def stats(self) -> dict[str, int]:
        """Provider usage statistics."""
        return {
            "requests": self._request_count,
            "errors": self._error_count,
        }

    def _track_request(self) -> None:
        """Track successful request."""
        self._request_count += 1

    def _track_error(self) -> None:
        """Track failed request."""
        self._error_count += 1

    @abstractmethod
    async def health_check(self) -> ProviderResponse[bool]:
        """Check if provider is available.

        Returns:
            ProviderResponse with True if healthy, False otherwise.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close provider connections and cleanup resources."""
        pass

    def _create_response(
        self,
        data: T | None,
        success: bool,
        error_message: str | None = None,
        error_code: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ProviderResponse[T]:
        """Create standardized response.

        Args:
            data: Response data
            success: Whether request was successful
            error_message: Error description if failed
            error_code: Error code for categorization
            metadata: Additional response metadata

        Returns:
            Normalized ProviderResponse
        """
        return ProviderResponse(
            data=data,
            success=success,
            provider=self._name,
            error_message=error_message,
            error_code=error_code,
            metadata=metadata or {},
        )
