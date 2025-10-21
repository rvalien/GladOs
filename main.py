import asyncio
import logging
import os
import sys
from aiogram import Bot, types, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command, CommandStart
from dotenv import load_dotenv
from utils import admin, coinflip, weather

load_dotenv()

VERSION = os.environ["RELEASE_VERSION"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
WEATHER_TOKEN = os.environ["WEATHER_TOKEN"]
router = Router()


@router.message(Command("help"))
async def help_command(message: types.Message):
    print(f"Получена команда help от {message.from_user.id}")
    await message.answer("✅ Помощь работает!")


storage = MemoryStorage()
dp = Dispatcher(storage=storage)
dp.include_router(router)
dp.include_router(admin.help_router)
dp.include_router(weather.router)
dp.include_router(admin.admin_router)
dp.include_router(coinflip.router)


@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    await message.reply(f"Hello, i'm GladOS. v{VERSION} beep boop...\n")


async def main() -> None:
    bot = Bot(
        token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
