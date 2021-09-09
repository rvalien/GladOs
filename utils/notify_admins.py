import logging
import os
import json
from aiogram import Dispatcher

ADMIN = json.loads(os.environ['ADMIN'])


async def on_startup_notify(dp: Dispatcher):
    try:
        await dp.bot.send_message(ADMIN, "Бот Запущен")

    except Exception as err:
        logging.exception(err)
