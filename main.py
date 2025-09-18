import asyncio
import logging
import os
import sys
from aiogram import Bot, types, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart

from utils import weather


VERSION = os.environ['RELEASE_VERSION']
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]

storage = MemoryStorage()
dp = Dispatcher(storage=storage)
dp.include_router(weather.router)

@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    logging.warning("Starting connection.")
    await message.reply(f"Hello, i'm GladOS. v{VERSION} beep boop...\n")


async def main() -> None:
    bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())