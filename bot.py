"""
this bot made with ❤️
"""

__author__ = "Valien"
__version__ = "2021.9.9"
__maintainer__ = "Valien"
__link__ = "https://github.com/rvalien/GladOs"

import aioschedule as schedule
import asyncio
import datetime
import logging
import os
import redis

# import pika
from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import ParseMode
from aiogram.utils import executor, markdown as md
from states import HomeForm

from keyboards import markup
from utils import redis_utils, mobile_utils, weather
from utils.db_api.db_gino import db, Flat, User, on_startup as gino_on_startup

redis_url = os.getenv("REDISTOGO_URL", "redis://localhost:6379")
telegram_token = os.environ["TELEGRAM_TOKEN"]
weather_token = os.environ["WEATHER_TOKEN"]
database = os.environ["DATABASE_URL"]
delay = int(os.environ["DELAY"])

# # mqtt
# url = os.environ.get("CLOUDAMQP_URL")
# params = pika.URLParameters(url)
# connections = pika.BlockingConnection(params)
# channel = connections.channel()
#
# channel.exchange_declare("test_exchange")
# # channel.queue_declare("mqtt-subscription-ESP8266qos0", auto_delete=False)
# channel.queue_bind("mqtt-subscription-ESP8266qos0", "test_exchange", "led_on_off")

bot = Bot(token=telegram_token)
storage = MemoryStorage()
dispatcher = Dispatcher(bot, storage=storage)
dispatcher.middleware.setup(LoggingMiddleware())

CLIENT = redis.from_url(redis_url)


@dispatcher.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    logging.warning("Starting connection.")
    await types.ChatActions.typing(0.5)
    await message.reply("Hello, i'm GladOS. beep boop...\n", reply_markup=markup)


@dispatcher.message_handler(Text(equals="weather"))
async def weather_worker(message):
    await types.ChatActions.typing(0.5)
    await message.reply(weather.get_weather(weather_token))


@dispatcher.message_handler(commands=["rest"])
async def free_time_worker(message):
    await types.ChatActions.typing(0.5)
    await message.reply(redis_utils.its_time_to(message, CLIENT, "rest"))


@dispatcher.message_handler(commands=["work"])
async def work_time_worker(message):
    await types.ChatActions.typing(0.5)
    await message.reply(redis_utils.its_time_to(message, CLIENT, "work"))


@dispatcher.message_handler(Text(equals="internet"))
async def internet_left_worker(message):
    await types.ChatActions.typing(1)
    user = await User.get(message.from_user.id)
    await message.reply(mobile_utils.get_internet_limit_text(user))


@dispatcher.message_handler(Text(equals="bill"))
async def get_bill_worker(message):
    await types.ChatActions.typing(1)
    users = await User.query.gino.all()
    await message.reply(mobile_utils.get_all_bills_text(users))


@dispatcher.message_handler(commands=["log"])
async def get_free_time_log_worker(message):
    await types.ChatActions.typing(0.5)

    users = await User.query.gino.all()
    chat_ids = list(map(lambda x: x.chat_id, users))
    await message.reply(redis_utils.usage_log(chat_ids, CLIENT))


@dispatcher.message_handler(commands=["myid"])
async def debug_worker(message):
    await types.ChatActions.typing(0.5)
    await message.reply(message.from_user)


@dispatcher.message_handler(Text(equals="🏡"))
async def meter_reading(message: types.Message):
    await types.ChatActions.typing(0.5)
    await HomeForm.t.set()

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["cancel"]
    keyboard.add(*buttons)
    welcome_message = """
    Передача показаний ПУ.\nДля прекращения операции - напиши `cancel` или нажми кнопку `cancel`.\nВнеси потребление ⚡ T
    """
    await message.reply(welcome_message, reply_markup=keyboard)


@dispatcher.message_handler(Text(equals="cancel", ignore_case=True), state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.finish()
    await types.ChatActions.typing(0.5)
    await message.reply("ОК", reply_markup=markup)


@dispatcher.message_handler(lambda message: message.text.isdigit(), state=HomeForm.t)
async def process_t(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.reply("введено не число")

    async with state.proxy() as data:
        data["t"] = int(message.text)

    await HomeForm.next()
    await message.reply("чудно, а теперь потребление ⚡T1")


@dispatcher.message_handler(lambda message: message.text.isdigit(), state=HomeForm.t1)
async def process_t1(message: types.Message, state: FSMContext):
    await HomeForm.next()
    await state.update_data(t1=int(message.text))
    await message.reply("чудно, а теперь потребление ⚡T2")


@dispatcher.message_handler(lambda message: message.text.isdigit(), state=HomeForm.t2)
async def process_t2(message: types.Message, state: FSMContext):
    await HomeForm.next()
    await state.update_data(t2=int(message.text))
    await message.reply("славно, а теперь потребление 🥶🌊")


@dispatcher.message_handler(lambda message: message.text.isdigit(), state=HomeForm.cold)
async def process_cold_water(message: types.Message, state: FSMContext):
    await HomeForm.next()
    await state.update_data(cold=int(message.text))
    await message.reply("и наконец, внеси потребление 🥵🌊")


# @dispatcher.message_handler(commands=["test"])
@dispatcher.message_handler(lambda message: message.text.isdigit(), state=HomeForm.hot)
async def process_hot_water(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["hot"] = int(message.text)

    # previous_data
    last_dt = await db.first(db.text("select date from flat order by date desc LIMIT 1"))
    last_dt = last_dt[0]
    pd = await Flat.query.where(Flat.date == last_dt).gino.first()
    alarm_limit = 5
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="передать показания", callback_data="save_to_db"))
    # TODO перенести проверку вводимых показаний на этап их ввода и там же показывать старые данные
    await message.answer(
        md.text(
            md.text("эл. энергия T:", md.code(data["t"]), f"❌ предыдущие {md.code(pd.t)}" if (
                    data["t"] <= pd.t or (data["t"] - pd.t) > alarm_limit) else "✔️"),
            md.text("эл. энергия T1:", md.code(data["t1"]), f"❌ предыдущие {md.code(pd.t1)}" if (
                    data["t1"] <= pd.t1 or (data["t1"] - pd.t1) > alarm_limit) else "✔️"),
            md.text("эл. энергия T2:", md.code(data["t2"]), f"❌ предыдущие {md.code(pd.t2)}" if (
                    data["t2"] <= pd.t2 or (data["t2"] - pd.t2) > alarm_limit) else "✔️"),
            md.text("холодная вода:", md.code(data["cold"]), f"❌ предыдущие {md.code(pd.cold)}" if (
                    data["cold"] <= pd.cold or (data["cold"] - pd.cold) > alarm_limit) else "✔️"),
            md.text("горячая вода:", md.code(data["hot"]), f"❌ предыдущие {md.code(pd.hot)}" if (
                    data["hot"] <= pd.hot or (data["hot"] - pd.hot) > alarm_limit) else "✔️"),
            sep="\n",
        ),
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )
    await HomeForm.next()


@dispatcher.callback_query_handler(text="save_to_db", state=HomeForm.date)
async def save_to_db(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data["date"] = datetime.datetime.now().date()

        flat_data = await Flat.get(data["date"])
        if flat_data:
            await flat_data.update(**data).apply()
        else:
            await Flat.create(**data)

    await call.message.answer(f"{data['date'].strftime('%Y %m %d')} saved", reply_markup=markup)
    # await call.answer(text="Спасибо, что воспользовались ботом!")
    await state.finish()


def repeat(coro, loop):
    asyncio.ensure_future(coro(), loop=loop)
    loop.call_later(delay, repeat, coro, loop)


async def scheduler():
    while True:
        await schedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(dispatcher):
    # import filters
    # import middlewares
    # filters.setup(dp)
    # middlewares.setup(dp)

    from utils.notify_admins import on_startup_notify

    await gino_on_startup(dispatcher)
    await on_startup_notify(dispatcher)
    # Запускает таймер для первой игры
    asyncio.create_task(scheduler())
    logging.info("Done")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    logging.basicConfig(level=logging.INFO)
    # loop.call_later(delay, repeat, some_task, loop)
    asyncio.run(executor.start_polling(dispatcher, on_startup=on_startup, loop=loop, skip_updates=True))
