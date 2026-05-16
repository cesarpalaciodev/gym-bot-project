"""Providers package for external API abstractions.

This package provides standardized interfaces for all external service
integrations including:
- Telegram Bot API
- MongoDB Database
- Error handling and retry logic
- Response normalization
"""

from __future__ import annotations

from providers.base import BaseProvider
from providers.database_provider import DatabaseProvider
from providers.exceptions import (
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderError,
    ProviderNotFoundError,
    ProviderRateLimitError,
    ProviderServerError,
    ProviderTimeoutError,
    ProviderValidationError,
)
from providers.response import ProviderResponse, error_response, success_response
from providers.retry_config import RetryConfig
from providers.telegram_provider import TelegramProvider

__all__ = [
    # Base classes
    "BaseProvider",
    # Providers
    "TelegramProvider",
    "DatabaseProvider",
    # Exceptions
    "ProviderError",
    "ProviderConnectionError",
    "ProviderTimeoutError",
    "ProviderRateLimitError",
    "ProviderAuthenticationError",
    "ProviderNotFoundError",
    "ProviderValidationError",
    "ProviderServerError",
    # Response
    "ProviderResponse",
    "success_response",
    "error_response",
    # Retry
    "RetryConfig",
]
