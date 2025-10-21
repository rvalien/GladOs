import pytest
import os
from unittest.mock import MagicMock, AsyncMock
from aiogram import types


@pytest.fixture(autouse=True)
def setup_env():
    """Автоматическая настройка переменных окружения для всех тестов"""
    os.environ["RELEASE_VERSION"] = "1.0.0"
    os.environ["TELEGRAM_TOKEN"] = "test_token_12345"
    os.environ["WEATHER_TOKEN"] = "test_weather_token"
    yield
    # Очистка после тестов не требуется, так как это тестовое окружение


@pytest.fixture
def message():
    """Фикстура для мокирования сообщения Telegram"""
    msg = MagicMock(spec=types.Message)

    # Настройка from_user
    msg.from_user = MagicMock()
    msg.from_user.id = 12345
    msg.from_user.first_name = "Test"
    msg.from_user.last_name = "User"
    msg.from_user.username = "testuser"

    # Настройка chat
    msg.chat = MagicMock()
    msg.chat.id = 12345
    msg.chat.type = "private"
    msg.chat.title = None
    msg.chat.username = None

    # Настройка методов
    msg.reply = AsyncMock()
    msg.answer = AsyncMock()
    msg.delete = AsyncMock()

    # Настройка бота
    msg.bot = MagicMock()
    msg.bot.send_message = AsyncMock()
    msg.bot.send_chat_action = AsyncMock()
    msg.bot.get_chat = AsyncMock()

    return msg


@pytest.fixture
def bot():
    """Фикстура для мокирования бота"""
    bot_mock = MagicMock()
    bot_mock.send_message = AsyncMock()
    bot_mock.send_chat_action = AsyncMock()
    bot_mock.get_chat = AsyncMock()
    bot_mock.get_me = AsyncMock()
    return bot_mock


@pytest.fixture
def callback_query():
    """Фикстура для мокирования callback query"""
    callback = MagicMock()
    callback.id = "test_callback_id"
    callback.from_user = MagicMock()
    callback.from_user.id = 12345
    callback.message = MagicMock(spec=types.Message)
    callback.message.chat = MagicMock()
    callback.message.chat.id = 12345
    callback.answer = AsyncMock()
    callback.message.edit_text = AsyncMock()
    callback.message.delete = AsyncMock()
    return callback


# Настройка pytest для асинхронных тестов
pytest_plugins = ("pytest_asyncio",)
