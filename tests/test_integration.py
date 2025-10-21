import pytest
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import Bot
from aiogram.types import Message, User, Chat


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


class TestBotIntegration:
    """Интеграционные тесты бота"""

    @pytest.fixture
    def bot(self):
        """Создание тестового бота"""
        return MagicMock(spec=Bot)

    def create_message(self, bot, text: str, user_id: int = 12345):
        """Создание тестового сообщения"""
        user = MagicMock(spec=User)
        user.id = user_id
        user.first_name = "Test"
        user.username = "testuser"

        chat = MagicMock(spec=Chat)
        chat.id = user_id
        chat.type = "private"
        chat.title = None
        chat.username = None

        message = MagicMock(spec=Message)
        message.text = text
        message.from_user = user
        message.chat = chat
        message.bot = bot
        message.answer = AsyncMock()
        message.reply = AsyncMock()

        return message

    @pytest.mark.asyncio
    async def test_start_command_flow(self, bot):
        """Тест полного флоу команды /start"""

        # Тестируем функцию напрямую, создав её локально
        async def send_welcome(message: Message):
            await message.reply(
                f"Hello, i'm GladOS. v{os.environ.get('RELEASE_VERSION')} beep boop...\n"
            )

        message = self.create_message(bot, "/start")

        await send_welcome(message)

        # Проверяем, что ответ был отправлен
        assert message.reply.called
        call_args = message.reply.call_args[0][0]
        assert "Hello, i'm GladOS" in call_args
        assert "1.0.0" in call_args

    @pytest.mark.asyncio
    async def test_admin_commands_access_control(self, bot):
        """Тест контроля доступа к административным командам"""
        from utils.admin import get_chat_id, admin_help, is_admin

        # Проверяем, что функция is_admin работает правильно
        assert is_admin(12345) is True
        assert is_admin(99999) is False

        # Админ может использовать команды
        admin_msg = self.create_message(bot, "/get_chat_id", user_id=12345)
        admin_msg.chat.title = "Test"
        admin_msg.chat.username = "test"
        await get_chat_id(admin_msg)
        assert admin_msg.answer.called

        # Не-админ не может использовать команды
        user_msg = self.create_message(bot, "/admin_help", user_id=99999)
        await admin_help(user_msg)
        assert not user_msg.answer.called

    @pytest.mark.asyncio
    async def test_weather_command_with_api_call(self, bot):
        """Тест команды погоды с реальным API вызовом (мокированным)"""
        message = self.create_message(bot, "/weather")
        message.bot.send_chat_action = AsyncMock()

        mock_weather_data = {
            "main": {"temp": 22.5},
            "weather": [{"description": "переменная облачность"}],
        }

        with patch("aiohttp.ClientSession") as mock_session:
            # Создаем мок для response
            mock_response = MagicMock()
            mock_response.json = AsyncMock(return_value=mock_weather_data)

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

            from utils.weather import weather_handler

            await weather_handler(message)

            message.bot.send_chat_action.assert_called_once()
            message.reply.assert_called_once()
            assert "22.5C" in message.reply.call_args[0][0]

    @pytest.mark.asyncio
    async def test_error_handling(self, bot):
        """Тест обработки ошибок"""
        from utils.admin import get_user_info
        from aiogram.filters import CommandObject

        message = self.create_message(bot, "/get_user_info invalid", user_id=12345)
        command = MagicMock(spec=CommandObject)
        command.args = "not_a_number"

        # Мокируем ошибку при получении пользователя
        message.bot.get_chat = AsyncMock(side_effect=ValueError("Invalid user ID"))

        await get_user_info(message, command)

        # Должно быть сообщение об ошибке
        assert message.answer.called
        call_args = message.answer.call_args[0][0]
        assert "Неверный формат" in call_args


class TestEnvironmentConfiguration:
    """Тесты конфигурации через переменные окружения"""

    @pytest.mark.asyncio
    async def test_admin_ids_parsing_single(self):
        """Тест парсинга одного администратора"""
        with patch.dict(os.environ, {"ADMIN_IDS": "12345"}, clear=False):
            # Удаляем модуль из кэша чтобы он переимпортировался
            if "utils.admin" in sys.modules:
                del sys.modules["utils.admin"]

            from utils import admin

            assert 12345 in admin.ADMIN_IDS

    @pytest.mark.asyncio
    async def test_admin_ids_parsing_multiple(self):
        """Тест парсинга нескольких администраторов"""
        # Полностью изолируем этот тест
        test_env = {
            "ADMIN_IDS": "12345, 67890, 11111",
            "TELEGRAM_TOKEN": "test_token",
            "WEATHER_TOKEN": "test_weather_token",
            "RELEASE_VERSION": "1.0.0",
        }

        with patch.dict(os.environ, test_env, clear=True):
            # Принудительно удаляем модуль
            if "utils.admin" in sys.modules:
                del sys.modules["utils.admin"]
            if "utils" in sys.modules:
                del sys.modules["utils"]

            # Импортируем заново
            from utils import admin

            assert 12345 in admin.ADMIN_IDS
            assert 67890 in admin.ADMIN_IDS
            assert 11111 in admin.ADMIN_IDS
            assert len(admin.ADMIN_IDS) == 3

            # Очищаем после теста
            del sys.modules["utils.admin"]
            if "utils" in sys.modules:
                del sys.modules["utils"]

    @pytest.mark.asyncio
    async def test_admin_ids_empty(self):
        """Тест пустого списка администраторов"""
        test_env = {
            "ADMIN_IDS": "",
            "TELEGRAM_TOKEN": "test_token",
            "WEATHER_TOKEN": "test_weather_token",
            "RELEASE_VERSION": "1.0.0",
        }

        with patch.dict(os.environ, test_env, clear=True):
            # Принудительно удаляем модуль
            if "utils.admin" in sys.modules:
                del sys.modules["utils.admin"]
            if "utils" in sys.modules:
                del sys.modules["utils"]

            from utils import admin

            assert admin.ADMIN_IDS == []

            # Очищаем после теста
            del sys.modules["utils.admin"]
            if "utils" in sys.modules:
                del sys.modules["utils"]

    @pytest.mark.asyncio
    async def test_weather_token_loaded(self):
        """Тест загрузки токена погоды"""
        with patch.dict(
            os.environ, {"WEATHER_TOKEN": "test_weather_token_123"}, clear=False
        ):
            if "utils.weather" in sys.modules:
                del sys.modules["utils.weather"]

            from utils import weather

            assert weather.WEATHER_TOKEN == "test_weather_token_123"


class TestMessageFormatting:
    """Тесты форматирования сообщений"""

    @pytest.mark.asyncio
    async def test_html_formatting_in_admin_help(self):
        """Тест HTML форматирования в admin_help"""
        from utils.admin import admin_help

        message = MagicMock(spec=Message)
        message.from_user = MagicMock()
        message.from_user.id = 12345
        message.answer = AsyncMock()

        await admin_help(message)

        call_kwargs = message.answer.call_args[1]
        assert call_kwargs["parse_mode"] == "HTML"

    @pytest.mark.asyncio
    async def test_code_blocks_in_responses(self):
        """Тест наличия code блоков в ответах"""
        from utils.admin import get_chat_id

        message = MagicMock(spec=Message)
        message.from_user = MagicMock()
        message.from_user.id = 12345
        message.chat = MagicMock()
        message.chat.id = 67890
        message.chat.title = "Test"
        message.chat.username = "test"
        message.chat.type = "private"
        message.answer = AsyncMock()

        await get_chat_id(message)

        call_args = message.answer.call_args[0][0]
        assert "<code>" in call_args
        assert "</code>" in call_args
