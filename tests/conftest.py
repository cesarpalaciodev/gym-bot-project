from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_update():
    update = MagicMock()
    update.effective_user.id = 12345
    update.effective_user.username = "testuser"
    update.effective_chat.type = "private"
    update.effective_chat.id = -100123
    update.message.text = ""
    update.message.reply_text = AsyncMock()
    update.message.reply_document = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    context = MagicMock()
    context.user_data = {}
    context.bot.get_chat_member = AsyncMock()
    return context


@pytest.fixture
def mock_collection():
    col = AsyncMock()
    col.find_one = AsyncMock()
    col.find = MagicMock()
    col.find.return_value.to_list = AsyncMock(return_value=[])
    col.insert_one = AsyncMock()
    col.delete_one = AsyncMock()
    col.delete_many = AsyncMock()
    col.update_one = AsyncMock()
    col.count_documents = AsyncMock(return_value=0)
    return col


@pytest.fixture
def patch_get_collection(mock_collection):
    with patch("database.get_collection", AsyncMock(return_value=mock_collection)) as mock:
        yield mock
