"""MongoDB database provider with retry and error handling."""

from __future__ import annotations

import logging
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import (
    ConnectionFailure,
    DuplicateKeyError,
    NetworkTimeout,
    OperationFailure,
    ServerSelectionTimeoutError,
)
from tenacity import retry

from config import MONGO_URI
from providers.base import BaseProvider
from providers.exceptions import (
    ERROR_CODES,
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderNotFoundError,
    ProviderServerError,
    ProviderTimeoutError,
    ProviderValidationError,
)
from providers.response import ProviderResponse, success_response, error_response
from providers.retry_config import RetryConfig

logger = logging.getLogger(__name__)


class DatabaseProvider(BaseProvider[Any]):
    """Provider for MongoDB database operations.

    Wraps Motor/MongoDB with standardized error handling,
    retries, and response normalization.
    """

    def __init__(self, mongo_uri: str | None = None) -> None:
        super().__init__("mongodb")
        self._mongo_uri = mongo_uri or MONGO_URI
        self._client: AsyncIOMotorClient | None = None
        self._db = None

    async def _get_client(self) -> AsyncIOMotorClient:
        """Get or create MongoDB client."""
        if self._client is None:
            if not self._mongo_uri:
                raise ProviderConnectionError(
                    "MONGO_URI not configured",
                    provider=self.name,
                    error_code=ERROR_CODES["CONNECTION_REFUSED"],
                )

            try:
                self._client = AsyncIOMotorClient(
                    self._mongo_uri,
                    maxPoolSize=10,
                    minPoolSize=1,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000,
                )
                self._db = self._client.get_database()
            except Exception as e:
                raise ProviderConnectionError(
                    f"Failed to create MongoDB client: {e}",
                    provider=self.name,
                    error_code=ERROR_CODES["CONNECTION_REFUSED"],
                    original_error=e,
                )

        return self._client

    def _handle_mongo_error(self, error: Exception, operation: str) -> Exception:
        """Convert MongoDB errors to provider exceptions.

        Args:
            error: Original MongoDB error
            operation: Operation being performed

        Returns:
            Provider exception
        """
        error_msg = str(error).lower()

        # Connection errors
        if isinstance(error, (ConnectionFailure, ServerSelectionTimeoutError)):
            return ProviderConnectionError(
                f"MongoDB connection failed during {operation}: {error}",
                provider=self.name,
                error_code=ERROR_CODES["CONNECTION_REFUSED"],
                original_error=error,
            )

        # Timeout
        if isinstance(error, NetworkTimeout):
            return ProviderTimeoutError(
                f"MongoDB timeout during {operation}: {error}",
                provider=self.name,
                error_code=ERROR_CODES["TIMEOUT"],
                original_error=error,
            )

        # Authentication
        if isinstance(error, OperationFailure) and any(x in error_msg for x in ["auth", "authentication"]):
            return ProviderAuthenticationError(
                f"MongoDB authentication failed: {error}",
                provider=self.name,
                error_code=ERROR_CODES["AUTH_FAILED"],
                original_error=error,
            )

        # Duplicate key
        if isinstance(error, DuplicateKeyError):
            return ProviderValidationError(
                f"Duplicate key error during {operation}: {error}",
                provider=self.name,
                error_code=ERROR_CODES["VALIDATION"],
                original_error=error,
            )

        # Server errors (5xx equivalent)
        if isinstance(error, OperationFailure):
            return ProviderServerError(
                f"MongoDB operation failed during {operation}: {error}",
                provider=self.name,
                error_code=ERROR_CODES["SERVER_ERROR"],
                original_error=error,
            )

        # Unknown
        return ProviderServerError(
            f"Unknown MongoDB error during {operation}: {error}",
            provider=self.name,
            error_code=ERROR_CODES["UNKNOWN"],
            original_error=error,
        )

    @retry(**RetryConfig.aggressive())  # Aggressive retry for DB
    async def ping(self) -> ProviderResponse[bool]:
        """Ping database to check connectivity.

        Returns:
            ProviderResponse with True if connected
        """
        self._track_request()

        try:
            client = await self._get_client()
            await client.admin.command("ping")

            return success_response(
                data=True,
                provider=self.name,
            )

        except Exception as e:
            self._track_error()
            provider_error = self._handle_mongo_error(e, "ping")

            return error_response(
                error_message=str(provider_error),
                provider=self.name,
                error_code=provider_error.error_code,
            )

    @retry(**RetryConfig.aggressive())
    async def find_one(
        self,
        collection: str,
        filter_dict: dict[str, Any],
    ) -> ProviderResponse[dict[str, Any] | None]:
        """Find single document.

        Args:
            collection: Collection name
            filter_dict: Query filter

        Returns:
            ProviderResponse with document or None
        """
        self._track_request()

        try:
            client = await self._get_client()
            db = client.get_database()
            result = await db[collection].find_one(filter_dict)

            return success_response(
                data=result,
                provider=self.name,
                metadata={"collection": collection},
            )

        except Exception as e:
            self._track_error()
            provider_error = self._handle_mongo_error(e, "find_one")

            return error_response(
                error_message=str(provider_error),
                provider=self.name,
                error_code=provider_error.error_code,
                metadata={"collection": collection},
            )

    @retry(**RetryConfig.aggressive())
    async def find_many(
        self,
        collection: str,
        filter_dict: dict[str, Any] | None = None,
        sort: list[tuple[str, int]] | None = None,
        limit: int | None = None,
    ) -> ProviderResponse[list[dict[str, Any]]]:
        """Find multiple documents.

        Args:
            collection: Collection name
            filter_dict: Query filter
            sort: Sort specification
            limit: Max results

        Returns:
            ProviderResponse with document list
        """
        self._track_request()

        try:
            client = await self._get_client()
            db = client.get_database()
            cursor = db[collection].find(filter_dict or {})

            if sort:
                cursor = cursor.sort(sort)
            if limit:
                cursor = cursor.limit(limit)

            results = await cursor.to_list(length=None)

            return success_response(
                data=results,
                provider=self.name,
                metadata={
                    "collection": collection,
                    "count": len(results),
                },
            )

        except Exception as e:
            self._track_error()
            provider_error = self._handle_mongo_error(e, "find_many")

            return error_response(
                error_message=str(provider_error),
                provider=self.name,
                error_code=provider_error.error_code,
                metadata={"collection": collection},
            )

    @retry(**RetryConfig.aggressive())
    async def insert_one(
        self,
        collection: str,
        document: dict[str, Any],
    ) -> ProviderResponse[str]:
        """Insert single document.

        Args:
            collection: Collection name
            document: Document to insert

        Returns:
            ProviderResponse with inserted ID
        """
        self._track_request()

        try:
            client = await self._get_client()
            db = client.get_database()
            result = await db[collection].insert_one(document)

            return success_response(
                data=str(result.inserted_id),
                provider=self.name,
                metadata={"collection": collection},
            )

        except Exception as e:
            self._track_error()
            provider_error = self._handle_mongo_error(e, "insert_one")

            return error_response(
                error_message=str(provider_error),
                provider=self.name,
                error_code=provider_error.error_code,
                metadata={"collection": collection},
            )

    @retry(**RetryConfig.aggressive())
    async def update_one(
        self,
        collection: str,
        filter_dict: dict[str, Any],
        update_dict: dict[str, Any],
    ) -> ProviderResponse[bool]:
        """Update single document.

        Args:
            collection: Collection name
            filter_dict: Query filter
            update_dict: Update operations

        Returns:
            ProviderResponse with True if modified
        """
        self._track_request()

        try:
            client = await self._get_client()
            db = client.get_database()
            result = await db[collection].update_one(filter_dict, update_dict)

            return success_response(
                data=result.modified_count > 0,
                provider=self.name,
                metadata={
                    "collection": collection,
                    "modified": result.modified_count,
                },
            )

        except Exception as e:
            self._track_error()
            provider_error = self._handle_mongo_error(e, "update_one")

            return error_response(
                error_message=str(provider_error),
                provider=self.name,
                error_code=provider_error.error_code,
                metadata={"collection": collection},
            )

    @retry(**RetryConfig.aggressive())
    async def delete_one(
        self,
        collection: str,
        filter_dict: dict[str, Any],
    ) -> ProviderResponse[bool]:
        """Delete single document.

        Args:
            collection: Collection name
            filter_dict: Query filter

        Returns:
            ProviderResponse with True if deleted
        """
        self._track_request()

        try:
            client = await self._get_client()
            db = client.get_database()
            result = await db[collection].delete_one(filter_dict)

            return success_response(
                data=result.deleted_count > 0,
                provider=self.name,
                metadata={
                    "collection": collection,
                    "deleted": result.deleted_count,
                },
            )

        except Exception as e:
            self._track_error()
            provider_error = self._handle_mongo_error(e, "delete_one")

            return error_response(
                error_message=str(provider_error),
                provider=self.name,
                error_code=provider_error.error_code,
                metadata={"collection": collection},
            )

    async def health_check(self) -> ProviderResponse[bool]:
        """Check database health.

        Returns:
            ProviderResponse with health status
        """
        return await self.ping()

    async def close(self) -> None:
        """Close database connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
