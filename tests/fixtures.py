import os
import sys

import pytest
from aiogram import types, Bot, Dispatcher
from unittest.mock import MagicMock, AsyncMock, patch
from aiogram.fsm.storage.memory import MemoryStorage


@pytest.fixture
def bot():
    """Фикстура для мок бота"""
    return MagicMock(spec=Bot)


@pytest.fixture
def message(bot):
    """Фикстура для сообщения"""
    msg = MagicMock(spec=types.Message)
    msg.from_user = MagicMock(spec=types.User)
    msg.from_user.id = 12345
    msg.from_user.first_name = "Test"
    msg.from_user.username = "testuser"
    msg.chat = MagicMock(spec=types.Chat)
    msg.chat.id = 12345
    msg.chat.type = "private"
    msg.reply = AsyncMock()
    msg.bot = bot
    return msg


@pytest.fixture
def dispatcher():
    """Фикстура для диспетчера"""
    storage = MemoryStorage()
    return Dispatcher(storage=storage)


@pytest.fixture(autouse=True)
def setup_env():
    """Автоматически устанавливаем переменные окружения для всех тестов"""
    env_vars = {
        "TELEGRAM_TOKEN": "test_token",
        "RELEASE_VERSION": "1.0.0",
        "WEATHER_TOKEN": "test_weather_token",
        "ADMIN_IDS": "12345",
    }

    # Очищаем импортированные модули ПЕРЕД установкой новых env
    modules_to_reload = ["utils.admin", "utils.weather", "main"]
    for mod in modules_to_reload:
        if mod in sys.modules:
            del sys.modules[mod]
    with patch.dict(os.environ, env_vars, clear=False):
        yield

    # Очищаем снова после теста
    for mod in modules_to_reload:
        if mod in sys.modules:
            del sys.modules[mod]
