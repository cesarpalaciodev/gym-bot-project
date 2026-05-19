"""Telegram Bot API provider with retry and error handling."""

from __future__ import annotations

import logging
from typing import Any

from telegram import Bot
from telegram.error import (
    BadRequest,
    ChatMigrated,
    Forbidden,
    InvalidToken,
    NetworkError,
    RetryAfter,
    TelegramError,
    TimedOut,
)
from tenacity import retry

from config import TOKEN
from providers.base import BaseProvider
from providers.exceptions import (
    ERROR_CODES,
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderError,
    ProviderNotFoundError,
    ProviderRateLimitError,
    ProviderServerError,
    ProviderValidationError,
)
from providers.response import ProviderResponse, error_response, success_response
from providers.retry_config import RetryConfig

logger = logging.getLogger(__name__)


class TelegramProvider(BaseProvider[Any]):
    """Provider for Telegram Bot API operations.

    Wraps python-telegram-bot with standardized error handling,
    retries, and response normalization.
    """

    def __init__(self, token: str | None = None) -> None:
        super().__init__("telegram")
        resolved = token or TOKEN or ""
        self._token: str = resolved
        self._bot: Bot | None = None

    async def _get_bot(self) -> Bot:
        """Get or create bot instance."""
        if self._bot is None:
            self._bot = Bot(token=self._token)
        return self._bot

    def _handle_telegram_error(self, error: TelegramError) -> ProviderError:
        """Convert TelegramError to provider exceptions.

        Args:
            error: Original Telegram error

        Returns:
            Provider exception
        """
        error_msg = str(error).lower()

        # Rate limiting
        if isinstance(error, RetryAfter):
            retry_after = getattr(error, "retry_after", None)
            return ProviderRateLimitError(
                f"Rate limited by Telegram: {error}",
                provider=self.name,
                retry_after=retry_after,
                error_code=ERROR_CODES["RATE_LIMIT"],
                original_error=error,
            )

        # Network issues
        if isinstance(error, (NetworkError, TimedOut)):
            return ProviderConnectionError(
                f"Network error: {error}",
                provider=self.name,
                error_code=ERROR_CODES["TIMEOUT"],
                original_error=error,
            )

        # Authentication
        if isinstance(error, (InvalidToken, Forbidden)):
            return ProviderAuthenticationError(
                f"Authentication failed: {error}",
                provider=self.name,
                error_code=ERROR_CODES["AUTH_FAILED"],
                original_error=error,
            )

        # Not found
        if isinstance(error, (BadRequest, ChatMigrated)):
            if "chat not found" in error_msg or "message to delete not found" in error_msg:
                return ProviderNotFoundError(
                    f"Resource not found: {error}",
                    provider=self.name,
                    error_code=ERROR_CODES["NOT_FOUND"],
                    original_error=error,
                )
            return ProviderValidationError(
                f"Invalid request: {error}",
                provider=self.name,
                error_code=ERROR_CODES["VALIDATION"],
                original_error=error,
            )

        # Server errors (5xx from Telegram)
        return ProviderServerError(
            f"Telegram server error: {error}",
            provider=self.name,
            error_code=ERROR_CODES["SERVER_ERROR"],
            original_error=error,
        )

    @retry(**RetryConfig.default())  # type: ignore[untyped-decorator]
    async def send_message(
        self,
        chat_id: int | str,
        text: str,
        **kwargs: Any,
    ) -> ProviderResponse[dict[str, Any]]:
        """Send message to chat with retry.

        Args:
            chat_id: Target chat ID
            text: Message text
            **kwargs: Additional parameters (parse_mode, reply_markup, etc.)

        Returns:
            ProviderResponse with message data
        """
        self._track_request()

        try:
            bot = await self._get_bot()
            message = await bot.send_message(
                chat_id=chat_id,
                text=text,
                **kwargs,
            )

            return success_response(
                data={
                    "message_id": message.message_id,
                    "chat_id": chat_id,
                    "text": text,
                },
                provider=self.name,
                metadata={"timestamp": message.date},
            )

        except TelegramError as e:
            self._track_error()
            provider_error = self._handle_telegram_error(e)

            return error_response(
                error_message=str(provider_error),
                provider=self.name,
                error_code=provider_error.error_code,
                metadata={"original_error": str(e)},
            )

    @retry(**RetryConfig.no_retry())  # type: ignore[untyped-decorator]
    async def delete_message(
        self,
        chat_id: int | str,
        message_id: int,
    ) -> ProviderResponse[bool]:
        """Delete message.

        Args:
            chat_id: Chat ID
            message_id: Message to delete

        Returns:
            ProviderResponse with success status
        """
        self._track_request()

        try:
            bot = await self._get_bot()
            await bot.delete_message(chat_id=chat_id, message_id=message_id)

            return success_response(
                data=True,
                provider=self.name,
            )

        except TelegramError as e:
            self._track_error()
            provider_error = self._handle_telegram_error(e)

            return error_response(
                error_message=str(provider_error),
                provider=self.name,
                error_code=provider_error.error_code,
            )

    @retry(**RetryConfig.default())  # type: ignore[untyped-decorator]
    async def get_chat(self, chat_id: int | str) -> ProviderResponse[dict[str, Any]]:
        """Get chat information.

        Args:
            chat_id: Chat ID

        Returns:
            ProviderResponse with chat data
        """
        self._track_request()

        try:
            bot = await self._get_bot()
            chat = await bot.get_chat(chat_id)

            return success_response(
                data={
                    "id": chat.id,
                    "type": chat.type,
                    "title": chat.title,
                    "username": chat.username,
                },
                provider=self.name,
            )

        except TelegramError as e:
            self._track_error()
            provider_error = self._handle_telegram_error(e)

            return error_response(
                error_message=str(provider_error),
                provider=self.name,
                error_code=provider_error.error_code,
            )

    async def health_check(self) -> ProviderResponse[bool]:
        """Check if bot token is valid.

        Returns:
            ProviderResponse with health status
        """
        try:
            bot = await self._get_bot()
            me = await bot.get_me()

            return success_response(
                data=True,
                provider=self.name,
                metadata={"bot_username": me.username},
            )

        except Exception as e:
            return error_response(
                error_message=f"Health check failed: {e}",
                provider=self.name,
                error_code="HEALTH_CHECK_FAILED",
            )

    async def close(self) -> None:
        """Close bot connection."""
        if self._bot:
            await self._bot.close()
            self._bot = None
