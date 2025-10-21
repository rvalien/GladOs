import random
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("coinflip"))
async def coinflip_command(message: Message):
    """
    Бросок монетки с результатом орёл или решка
    """
    result = random.randint(0, 1)

    if result == 0:
        coin_side = "🪙 Орёл"
    else:
        coin_side = "🪙 Решка"

    await message.reply(f"🎲 Бросаем монетку...\n\n{coin_side}!")
