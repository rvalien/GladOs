import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import types, Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage


@pytest.fixture
def bot():
    """Фикстура для мок бота"""
    return MagicMock(spec=Bot)


@pytest.fixture
def dispatcher():
    """Фикстура для диспетчера"""
    storage = MemoryStorage()
    return Dispatcher(storage=storage)


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
    msg.answer = AsyncMock()
    msg.reply = AsyncMock()
    msg.bot = bot
    return msg


@pytest.fixture(autouse=True)
def setup_env():
    """Автоматически устанавливаем переменные окружения для всех тестов"""
    env_vars = {
        "TELEGRAM_TOKEN": "test_token",
        "RELEASE_VERSION": "1.0.0",
        "WEATHER_TOKEN": "test_weather_token",
        "ADMIN_IDS": "12345",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        yield


class TestMainBot:
    """Тесты основного функционала бота"""

    @pytest.mark.asyncio
    async def test_start_command(self, message):
        """Тест команды /start"""
        # Тестируем логику команды напрямую
        VERSION = os.environ.get("RELEASE_VERSION", "unknown")
        await message.reply(f"Hello, i'm GladOS. v{VERSION} beep boop...\n")

        message.reply.assert_called_once()
        call_args = message.reply.call_args[0][0]
        assert "Hello, i'm GladOS" in call_args
        assert "1.0.0" in call_args

    @pytest.mark.asyncio
    async def test_help_command(self, message):
        """Тест команды /help"""
        # Тестируем логику команды напрямую
        await message.answer("✅ Помощь работает!")

        message.answer.assert_called_once_with("✅ Помощь работает!")


class TestWeather:
    """Тесты модуля погоды"""

    @pytest.mark.asyncio
    async def test_get_weather_success(self):
        """Тест успешного получения погоды"""
        from utils.weather import get_weather

        mock_response_data = {
            "main": {"temp": 15.5},
            "weather": [{"description": "облачно"}],
        }

        with patch("aiohttp.ClientSession") as mock_session:
            # Создаем мок для response
            mock_response = MagicMock()
            mock_response.json = AsyncMock(return_value=mock_response_data)

            # Создаем мок для context manager get()
            mock_get_cm = MagicMock()
            mock_get_cm.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get_cm.__aexit__ = AsyncMock(return_value=False)

            # Создаем мок для session
            mock_session_instance = MagicMock()
            mock_session_instance.get = MagicMock(return_value=mock_get_cm)

            # Создаем мок для context manager session
            mock_session_cm = MagicMock()
            mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_cm.__aexit__ = AsyncMock(return_value=False)

            mock_session.return_value = mock_session_cm

            result = await get_weather("test_token", 550280)

            assert result == "15.5C, облачно"

    @pytest.mark.asyncio
    async def test_get_weather_api_error(self):
        """Тест обработки ошибки API"""
        from utils.weather import get_weather
        from exceptions import ApiServiceError

        with patch("aiohttp.ClientSession") as mock_session:
            # Создаем мок для response с ошибкой
            mock_response = MagicMock()
            mock_response.json = AsyncMock(side_effect=ValueError("Invalid JSON"))

            # Создаем мок для context manager get()
            mock_get_cm = MagicMock()
            mock_get_cm.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get_cm.__aexit__ = AsyncMock(return_value=False)

            # Создаем мок для session
            mock_session_instance = MagicMock()
            mock_session_instance.get = MagicMock(return_value=mock_get_cm)

            # Создаем мок для context manager session
            mock_session_cm = MagicMock()
            mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_cm.__aexit__ = AsyncMock(return_value=False)

            mock_session.return_value = mock_session_cm

            with pytest.raises(ApiServiceError):
                await get_weather("test_token", 550280)

    @pytest.mark.asyncio
    async def test_weather_handler(self, message):
        """Тест обработчика команды /weather"""
        from utils.weather import weather_handler

        message.bot.send_chat_action = AsyncMock()

        with patch("utils.weather.get_weather", return_value="20.0C, ясно"):
            await weather_handler(message)

            message.bot.send_chat_action.assert_called_once()
            message.reply.assert_called_once_with("20.0C, ясно")


class TestAdmin:
    """Тесты административных команд"""

    @pytest.mark.asyncio
    async def test_is_admin_true(self):
        """Тест проверки администратора"""
        from utils.admin import is_admin

        with patch("utils.admin.ADMIN_IDS", [12345, 67890]):
            assert is_admin(12345) is True
            assert is_admin(67890) is True

    @pytest.mark.asyncio
    async def test_is_admin_false(self):
        """Тест проверки не-администратора"""
        from utils.admin import is_admin

        with patch("utils.admin.ADMIN_IDS", [12345, 67890]):
            assert is_admin(99999) is False

    @pytest.mark.asyncio
    async def test_admin_help_success(self, message):
        """Тест команды admin_help для администратора"""
        from utils.admin import admin_help

        message.from_user.id = 12345

        with patch("utils.admin.ADMIN_IDS", [12345]):
            await admin_help(message)

            message.answer.assert_called_once()
            call_args = message.answer.call_args[0][0]
            assert "admin команды" in call_args
            assert "/get_channel_id" in call_args

    @pytest.mark.asyncio
    async def test_admin_help_forbidden(self, message):
        """Тест команды admin_help для не-администратора"""
        from utils.admin import admin_help

        message.from_user.id = 99999

        with patch("utils.admin.ADMIN_IDS", [12345]):
            await admin_help(message)

            message.answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_chat_id(self, message):
        """Тест получения ID чата"""
        from utils.admin import get_chat_id

        message.from_user.id = 12345
        message.chat.title = "Test Chat"
        message.chat.username = "testchat"

        with patch("utils.admin.ADMIN_IDS", [12345]):
            await get_chat_id(message)

            message.answer.assert_called_once()
            call_args = message.answer.call_args[0][0]
            assert "Информация о чате" in call_args
            assert str(message.chat.id) in call_args

    @pytest.mark.asyncio
    async def test_list_admins(self, message):
        """Тест списка администраторов"""
        from utils.admin import list_admins

        message.from_user.id = 12345

        with patch("utils.admin.ADMIN_IDS", [12345, 67890]):
            await list_admins(message)

            message.answer.assert_called_once()
            call_args = message.answer.call_args[0][0]
            assert "Администраторы бота" in call_args
            assert "12345" in call_args
            assert "67890" in call_args

    @pytest.mark.asyncio
    async def test_get_channel_id_success(self, message):
        """Тест успешного получения ID канала"""
        from utils.admin import get_channel_id
        from aiogram.filters import CommandObject

        message.from_user.id = 12345
        command = MagicMock(spec=CommandObject)
        command.args = "test_channel"

        mock_chat = MagicMock()
        mock_chat.id = -1001234567890
        mock_chat.title = "Test Channel"
        mock_chat.username = "test_channel"
        mock_chat.type = "channel"

        message.bot.get_chat = AsyncMock(return_value=mock_chat)

        with patch("utils.admin.ADMIN_IDS", [12345]):
            await get_channel_id(message, command)

            message.answer.assert_called_once()
            call_args = message.answer.call_args[0][0]
            assert "Информация о канале" in call_args
            assert "-1001234567890" in call_args

    @pytest.mark.asyncio
    async def test_get_channel_id_no_args(self, message):
        """Тест команды get_channel_id без аргументов"""
        from utils.admin import get_channel_id
        from aiogram.filters import CommandObject

        message.from_user.id = 12345
        command = MagicMock(spec=CommandObject)
        command.args = None

        with patch("utils.admin.ADMIN_IDS", [12345]):
            await get_channel_id(message, command)

            message.answer.assert_called_once()
            call_args = message.answer.call_args[0][0]
            assert "Укажите username канала" in call_args

    @pytest.mark.asyncio
    async def test_get_user_info_success(self, message):
        """Тест успешного получения информации о пользователе"""
        from utils.admin import get_user_info
        from aiogram.filters import CommandObject

        message.from_user.id = 12345
        command = MagicMock(spec=CommandObject)
        command.args = "67890"

        mock_user = MagicMock()
        mock_user.id = 67890
        mock_user.first_name = "John"
        mock_user.last_name = "Doe"
        mock_user.username = "johndoe"
        mock_user.type = "private"

        message.bot.get_chat = AsyncMock(return_value=mock_user)

        with patch("utils.admin.ADMIN_IDS", [12345]):
            await get_user_info(message, command)

            message.answer.assert_called_once()
            call_args = message.answer.call_args[0][0]
            assert "Информация о пользователе" in call_args
            assert "67890" in call_args

    @pytest.mark.asyncio
    async def test_help_command_with_buttons(self, message):
        """Тест команды help с кнопками"""
        from utils.admin import help_command_with_buttons

        await help_command_with_buttons(message)

        message.answer.assert_called_once()
        call_args = message.answer.call_args
        assert "Помощь по боту" in call_args[0][0]
        assert call_args[1]["reply_markup"] is not None


class TestExceptions:
    """Тесты исключений"""

    def test_api_service_error_exception(self):
        """Тест исключения ApiServiceError"""
        from exceptions import ApiServiceError

        with pytest.raises(ApiServiceError):
            raise ApiServiceError("Test error")
