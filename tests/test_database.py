from unittest.mock import MagicMock, patch

import pytest
from pymongo.errors import ConnectionFailure


class TestDatabaseInit:
    @patch("database.MONGO_URI", "mongodb://localhost:27017/test")
    @patch("database.MongoClient")
    def test_get_database_success(self, mock_client):
        mock_db = MagicMock()
        mock_client.return_value.get_database.return_value = mock_db

        from database import close_database, get_database
        close_database()

        db = get_database()
        assert db is not None

    @patch("database.MONGO_URI", "")
    def test_get_database_no_uri(self):
        from database import close_database, get_database
        close_database()
        with pytest.raises(ValueError, match="MONGO_URI no está configurado"):
            get_database()

    @patch("database.MONGO_URI", "mongodb://localhost:27017/test")
    @patch("database.MongoClient")
    def test_get_database_connection_failure(self, mock_client):
        mock_client.side_effect = ConnectionFailure("Failed")

        from database import close_database, get_database
        close_database()

        with pytest.raises(ConnectionFailure):
            get_database()

    def test_get_collection(self):
        from database import get_collection
        assert callable(get_collection)
