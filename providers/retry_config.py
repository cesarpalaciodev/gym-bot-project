"""Retry configuration for external API calls."""

from __future__ import annotations

import logging
from typing import Any, Callable

from tenacity import (
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from providers.exceptions import (
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderNotFoundError,
    ProviderRateLimitError,
    ProviderServerError,
    ProviderTimeoutError,
    ProviderValidationError,
)

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior.

    Provides pre-configured retry strategies for different scenarios.
    """

    # Retry on these exceptions
    DEFAULT_RETRY_EXCEPTIONS = (
        ProviderConnectionError,
        ProviderTimeoutError,
        ProviderServerError,
    )

    # Don't retry these (client errors)
    NO_RETRY_EXCEPTIONS = (
        ProviderAuthenticationError,
        ProviderNotFoundError,
        ProviderValidationError,
    )

    @staticmethod
    def default(
        max_attempts: int = 3,
        min_wait: int = 1,
        max_wait: int = 10,
    ) -> dict[str, Any]:
        """Default retry configuration.

        Args:
            max_attempts: Maximum retry attempts (default: 3)
            min_wait: Minimum wait seconds between retries (default: 1)
            max_wait: Maximum wait seconds between retries (default: 10)

        Returns:
            Dict with tenacity retry configuration
        """
        return {
            "stop": stop_after_attempt(max_attempts),
            "wait": wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            "retry": retry_if_exception_type(RetryConfig.DEFAULT_RETRY_EXCEPTIONS),
            "before_sleep": before_sleep_log(logger, logging.WARNING),
            "reraise": True,
        }

    @staticmethod
    def aggressive(
        max_attempts: int = 5,
        min_wait: int = 2,
        max_wait: int = 30,
    ) -> dict[str, Any]:
        """Aggressive retry for critical operations.

        Args:
            max_attempts: Maximum retry attempts (default: 5)
            min_wait: Minimum wait seconds (default: 2)
            max_wait: Maximum wait seconds (default: 30)

        Returns:
            Dict with aggressive retry configuration
        """
        return {
            "stop": stop_after_attempt(max_attempts),
            "wait": wait_exponential(multiplier=2, min=min_wait, max=max_wait),
            "retry": retry_if_exception_type(RetryConfig.DEFAULT_RETRY_EXCEPTIONS),
            "before_sleep": before_sleep_log(logger, logging.WARNING),
            "reraise": True,
        }

    @staticmethod
    def no_retry() -> dict[str, Any]:
        """No retry configuration for non-idempotent operations.

        Returns:
            Dict that disables retries
        """
        return {
            "stop": stop_after_attempt(1),
            "reraise": True,
        }

    @staticmethod
    def for_rate_limit(
        max_attempts: int = 3,
        base_wait: int = 5,
    ) -> dict[str, Any]:
        """Special retry for rate limit errors with longer waits.

        Args:
            max_attempts: Maximum retry attempts (default: 3)
            base_wait: Base wait time in seconds (default: 5)

        Returns:
            Dict with rate-limit-aware retry configuration
        """
        return {
            "stop": stop_after_attempt(max_attempts),
            "wait": wait_exponential(multiplier=base_wait, min=base_wait, max=60),
            "retry": retry_if_exception_type((ProviderRateLimitError,)),
            "before_sleep": before_sleep_log(logger, logging.WARNING),
            "reraise": True,
        }


def is_retryable_error(error: Exception) -> bool:
    """Check if an error should be retried.

    Args:
        error: The exception to check

    Returns:
        True if error is retryable
    """
    return isinstance(error, RetryConfig.DEFAULT_RETRY_EXCEPTIONS)


def get_retry_after(error: Exception) -> int | None:
    """Extract retry-after value from error if available.

    Args:
        error: The exception

    Returns:
        Seconds to wait before retry, or None
    """
    if isinstance(error, ProviderRateLimitError):
        return error.retry_after
    return None
