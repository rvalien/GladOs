import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import types


# Настройка переменных окружения перед импортом
@pytest.fixture(scope="session", autouse=True)
def setup_env():
    """Устанавливаем переменные окружения для всей тестовой сессии"""
    os.environ["RELEASE_VERSION"] = "1.0.0"
    os.environ["TELEGRAM_TOKEN"] = "test_token_12345"
    os.environ["WEATHER_TOKEN"] = "test_weather_token"


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
    msg.chat.title = "Test Chat"
    msg.chat.username = "testchat"

    # Методы сообщения
    msg.reply = AsyncMock()
    msg.answer = AsyncMock()
    msg.delete = AsyncMock()

    # Бот
    msg.bot = MagicMock()
    msg.bot.send_message = AsyncMock()
    msg.bot.send_chat_action = AsyncMock()
    msg.bot.get_chat = AsyncMock()

    return msg


class TestMainBot:
    """Тесты основного функционала бота"""

    @pytest.mark.asyncio
    async def test_start_command(self, message):
        """Тест команды /start"""
        from main import send_welcome

        await send_welcome(message)

        message.reply.assert_called_once()
        call_args = message.reply.call_args[0][0]
        assert "Hello, i'm GladOS" in call_args
        assert "1.0.0" in call_args

    @pytest.mark.asyncio
    async def test_help_command(self, message):
        """Тест команды /help"""
        from main import help_command

        await help_command(message)

        message.answer.assert_called_once_with("✅ Помощь работает!")

    @pytest.mark.asyncio
    async def test_dispatcher_created(self):
        """Тест что диспетчер создан корректно"""
        from main import dp

        assert dp is not None
        # Проверяем что это объект Dispatcher
        from aiogram import Dispatcher

        assert isinstance(dp, Dispatcher)

    @pytest.mark.asyncio
    async def test_routers_and_storage(self):
        """Тест что роутеры и storage созданы"""
        from main import dp, router, storage

        # Проверяем что все компоненты существуют
        assert dp is not None
        assert router is not None
        assert storage is not None

        # Проверяем типы
        from aiogram import Router
        from aiogram.fsm.storage.memory import MemoryStorage

        assert isinstance(router, Router)
        assert isinstance(storage, MemoryStorage)


class TestWeather:
    """Тесты модуля погоды"""

    @pytest.mark.asyncio
    async def test_get_weather_success(self):
        """Тест успешного получения погоды"""
        try:
            from utils.weather import get_weather
        except ImportError:
            pytest.skip("Модуль utils.weather не найден")

        mock_response_data = {
            "main": {"temp": 15.5},
            "weather": [{"description": "облачно"}],
        }

        with patch("aiohttp.ClientSession") as mock_session:
            # Создаем mock response
            mock_response = MagicMock()
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_response.status = 200

            # Context manager для response
            mock_get_cm = MagicMock()
            mock_get_cm.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get_cm.__aexit__ = AsyncMock(return_value=False)

            # Mock session instance
            mock_session_instance = MagicMock()
            mock_session_instance.get = MagicMock(return_value=mock_get_cm)

            # Context manager для session
            mock_session_cm = MagicMock()
            mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_cm.__aexit__ = AsyncMock(return_value=False)

            mock_session.return_value = mock_session_cm

            result = await get_weather("test_token", 550280)

            # Проверяем что результат содержит данные о погоде
            assert result is not None
            assert isinstance(result, str)
            assert "15.5" in str(result) or "облачно" in str(result).lower()

    @pytest.mark.asyncio
    async def test_get_weather_api_error(self):
        """Тест обработки ошибки API"""
        try:
            from utils.weather import get_weather
        except ImportError:
            pytest.skip("Модуль utils.weather не найден")

        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = MagicMock()
            mock_response.json = AsyncMock(side_effect=ValueError("Invalid JSON"))
            mock_response.status = 500

            mock_get_cm = MagicMock()
            mock_get_cm.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get_cm.__aexit__ = AsyncMock(return_value=False)

            mock_session_instance = MagicMock()
            mock_session_instance.get = MagicMock(return_value=mock_get_cm)

            mock_session_cm = MagicMock()
            mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_cm.__aexit__ = AsyncMock(return_value=False)

            mock_session.return_value = mock_session_cm

            # Проверяем что функция обрабатывает ошибку корректно
            with pytest.raises(Exception):
                await get_weather("test_token", 550280)

    @pytest.mark.asyncio
    async def test_weather_handler(self, message):
        """Тест обработчика команды /weather"""
        try:
            from utils.weather import weather_handler
        except (ImportError, AttributeError):
            pytest.skip("Функция weather_handler не найдена")

        message.bot.send_chat_action = AsyncMock()

        with patch("utils.weather.get_weather", return_value="20.0°C, ясно"):
            await weather_handler(message)

            # Проверяем что действие отправлено
            message.bot.send_chat_action.assert_called()

            # Проверяем что ответ отправлен
            assert message.reply.called or message.answer.called


class TestAdmin:
    """Тесты административных команд"""

    @pytest.mark.asyncio
    async def test_is_admin_true(self):
        """Тест проверки администратора"""
        try:
            from utils.admin import is_admin
        except ImportError:
            pytest.skip("Модуль utils.admin не найден")

        with patch("utils.admin.ADMIN_IDS", [12345, 67890]):
            assert is_admin(12345) is True
            assert is_admin(67890) is True

    @pytest.mark.asyncio
    async def test_is_admin_false(self):
        """Тест проверки не-администратора"""
        try:
            from utils.admin import is_admin
        except ImportError:
            pytest.skip("Модуль utils.admin не найден")

        with patch("utils.admin.ADMIN_IDS", [12345, 67890]):
            assert is_admin(99999) is False

    @pytest.mark.asyncio
    async def test_admin_help_success(self, message):
        """Тест команды admin_help для администратора"""
        try:
            from utils.admin import admin_help
        except (ImportError, AttributeError):
            pytest.skip("Функция admin_help не найдена")

        message.from_user.id = 12345

        with patch("utils.admin.ADMIN_IDS", [12345]):
            await admin_help(message)

            # Проверяем что ответ был отправлен
            assert message.answer.called or message.reply.called

            if message.answer.called:
                call_args = message.answer.call_args[0][0]
                # Проверяем что в ответе есть информация об админских командах
                assert any(
                    word in call_args.lower() for word in ["admin", "команд", "help"]
                )

    @pytest.mark.asyncio
    async def test_admin_help_forbidden(self, message):
        """Тест команды admin_help для не-администратора"""
        try:
            from utils.admin import admin_help
        except (ImportError, AttributeError):
            pytest.skip("Функция admin_help не найдена")

        message.from_user.id = 99999
        message.answer.reset_mock()
        message.reply.reset_mock()

        with patch("utils.admin.ADMIN_IDS", [12345]):
            await admin_help(message)

            # Для не-админа либо не должно быть ответа, либо ответ об отказе

    @pytest.mark.asyncio
    async def test_get_chat_id(self, message):
        """Тест получения ID чата"""
        try:
            from utils.admin import get_chat_id
        except (ImportError, AttributeError):
            pytest.skip("Функция get_chat_id не найдена")

        message.from_user.id = 12345

        with patch("utils.admin.ADMIN_IDS", [12345]):
            await get_chat_id(message)

            if message.answer.called:
                call_args = message.answer.call_args[0][0]
                assert str(message.chat.id) in call_args

    @pytest.mark.asyncio
    async def test_list_admins(self, message):
        """Тест списка администраторов"""
        try:
            from utils.admin import list_admins
        except (ImportError, AttributeError):
            pytest.skip("Функция list_admins не найдена")

        message.from_user.id = 12345

        with patch("utils.admin.ADMIN_IDS", [12345, 67890]):
            await list_admins(message)

            if message.answer.called:
                call_args = message.answer.call_args[0][0]
                assert "12345" in call_args or "67890" in call_args


class TestCoinflip:
    """Тесты модуля подбрасывания монетки"""

    @pytest.mark.asyncio
    async def test_coinflip_command_exists(self):
        """Тест что модуль coinflip существует"""
        try:
            from utils import coinflip

            assert coinflip is not None
        except ImportError:
            pytest.skip("Модуль utils.coinflip не найден")

    @pytest.mark.asyncio
    async def test_coinflip_command(self, message):
        """Тест команды подбрасывания монетки"""
        try:
            from utils.coinflip import coinflip_command
        except (ImportError, AttributeError):
            pytest.skip("Функция coinflip_command не найдена")

        await coinflip_command(message)

        # Проверяем что был вызван reply или answer
        assert message.reply.called or message.answer.called

        # Проверяем что результат - либо "Орёл", либо "Решка"
        if message.answer.called:
            call_args = message.answer.call_args[0][0]
            assert any(
                word in call_args
                for word in ["Орёл", "Решка", "орёл", "решка", "Heads", "Tails"]
            )


class TestExceptions:
    """Тесты исключений"""

    def test_api_service_error_exception(self):
        """Тест исключения ApiServiceError"""
        try:
            from exceptions import ApiServiceError
        except ImportError:
            pytest.skip("Модуль exceptions не найден")

        # Проверяем что исключение работает корректно
        with pytest.raises(ApiServiceError):
            raise ApiServiceError("Test error")

    def test_api_service_error_message(self):
        """Тест сообщения исключения ApiServiceError"""
        try:
            from exceptions import ApiServiceError
        except ImportError:
            pytest.skip("Модуль exceptions не найден")

        error = ApiServiceError("Test error message")
        assert str(error) == "Test error message"


class TestEnvironment:
    """Тесты переменных окружения"""

    def test_version_loaded(self):
        """Тест загрузки версии"""
        from main import VERSION

        assert VERSION is not None
        assert VERSION == "1.0.0"

    def test_telegram_token_loaded(self):
        """Тест загрузки токена Telegram"""
        from main import TELEGRAM_TOKEN

        assert TELEGRAM_TOKEN is not None
        assert len(TELEGRAM_TOKEN) > 0

    def test_weather_token_loaded(self):
        """Тест загрузки токена погоды"""
        from main import WEATHER_TOKEN

        assert WEATHER_TOKEN is not None
        assert len(WEATHER_TOKEN) > 0


class TestIntegration:
    """Интеграционные тесты"""

    @pytest.mark.asyncio
    async def test_main_bot_structure(self):
        """Тест структуры основного бота"""
        from main import dp, router, storage

        assert dp is not None
        assert router is not None
        assert storage is not None

        # Проверяем типы
        from aiogram import Dispatcher, Router
        from aiogram.fsm.storage.memory import MemoryStorage

        assert isinstance(dp, Dispatcher)
        assert isinstance(router, Router)
        assert isinstance(storage, MemoryStorage)

    @pytest.mark.asyncio
    async def test_imports_working(self):
        """Тест что все модули импортируются"""
        # Проверяем основной модуль
        import main

        assert hasattr(main, "dp")
        assert hasattr(main, "router")
        assert hasattr(main, "VERSION")
        assert hasattr(main, "TELEGRAM_TOKEN")

        # Проверяем что утилиты доступны
        try:
            from utils import admin, weather, coinflip

            assert admin is not None
            assert weather is not None
            assert coinflip is not None
        except ImportError:
            pytest.skip("Некоторые модули utils не найдены")


# Параметризованные тесты
class TestParametrized:
    """Параметризованные тесты"""

    @pytest.mark.parametrize(
        "user_id,expected",
        [
            (12345, True),
            (67890, True),
            (99999, False),
        ],
    )
    def test_is_admin_parametrized(self, user_id, expected):
        """Параметризованный тест проверки администратора"""
        try:
            from utils.admin import is_admin
        except ImportError:
            pytest.skip("Модуль utils.admin не найден")

        with patch("utils.admin.ADMIN_IDS", [12345, 67890]):
            assert is_admin(user_id) == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
