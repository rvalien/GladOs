import pytest
from unittest.mock import patch
from aiogram import types


class TestCoinFlip:
    """Тесты модуля монетки"""

    @pytest.mark.asyncio
    async def test_coin_flip_heads(self, message: types.Message):
        """Тест броска монетки с результатом Орёл"""
        from utils.coinflip import coinflip_command

        with patch("random.randint", return_value=0):
            await coinflip_command(message)

            message.reply.assert_called_once()
            call_args = message.reply.call_args[0][0]

            assert "🎲 Бросаем монетку..." in call_args
            assert "🪙 Орёл" in call_args

    @pytest.mark.asyncio
    async def test_coin_flip_tails(self, message: types.Message):
        """Тест броска монетки с результатом Решка"""
        from utils.coinflip import coinflip_command

        with patch("random.randint", return_value=1):
            await coinflip_command(message)

            message.reply.assert_called_once()
            call_args = message.reply.call_args[0][0]

            assert "🎲 Бросаем монетку..." in call_args
            assert "🪙 Решка" in call_args

    @pytest.mark.asyncio
    async def test_coin_flip_random_distribution(self, message: types.Message):
        """Тест проверки распределения результатов броска монетки"""
        from utils.coinflip import coinflip_command

        results = []

        with patch("random.randint") as mock_randint:
            mock_randint.return_value = 0
            await coinflip_command(message)
            call_args = message.reply.call_args[0][0]
            assert "🪙 Орёл" in call_args
            results.append("heads")

            mock_randint.return_value = 1
            await coinflip_command(message)
            call_args = message.reply.call_args[0][0]
            assert "🪙 Решка" in call_args
            results.append("tails")

        assert len(results) == 2
        assert "heads" in results
        assert "tails" in results

    @pytest.mark.asyncio
    async def test_coin_flip_message_format(self, message: types.Message):
        """Тест форматирования сообщения"""
        from utils.coinflip import coinflip_command

        with patch("random.randint", return_value=0):
            await coinflip_command(message)

            message.reply.assert_called_once()
            call_args = message.reply.call_args[0][0]

            assert call_args.startswith("🎲 Бросаем монетку...")
            assert "\n\n" in call_args
            assert "🪙 Орёл" in call_args or "🪙 Решка" in call_args
