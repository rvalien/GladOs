import json
import logging
import os

from keyboards import markup
from aiogram import Dispatcher

ADMIN = json.loads(os.environ['ADMIN'])


async def on_startup_notify(dp: Dispatcher):
    try:
        await dp.bot.send_message(ADMIN, "Бот Запущен", reply_markup=markup, disable_notification=True)

    except Exception as err:
        logging.exception(err)
