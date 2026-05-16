from unittest.mock import AsyncMock, patch

import pytest
from pymongo.errors import ConnectionFailure


@pytest.mark.asyncio
class TestDatabaseInit:
    @patch("database.MONGO_URI", "mongodb://localhost:27017/test")
    @patch("database.AsyncIOMotorClient")
    async def test_get_database_success(self, mock_client):
        mock_db = AsyncMock()
        mock_client.return_value.get_database.return_value = mock_db
        mock_db.command = AsyncMock()

        from database import close_database, get_database

        await close_database()

        db = await get_database()
        assert db is not None

    @patch("database.MONGO_URI", "")
    async def test_get_database_no_uri(self):
        from database import close_database, get_database

        await close_database()
        with pytest.raises(ValueError, match="MONGO_URI no está configurado"):
            await get_database()

    @patch("database.MONGO_URI", "mongodb://localhost:27017/test")
    @patch("database.AsyncIOMotorClient")
    async def test_get_database_connection_failure(self, mock_client):
        mock_client.side_effect = ConnectionFailure("Failed")

        from database import close_database, get_database

        await close_database()

        with pytest.raises(ConnectionFailure):
            await get_database()

    async def test_get_collection(self):
        from database import get_collection

        assert callable(get_collection)
