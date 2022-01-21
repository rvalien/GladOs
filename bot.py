"""
This bot made with ❤️
"""

__author__ = "Valien"
__version__ = "2022.1"
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
from states import HomeForm, BloodPressureForm
from asyncpg.exceptions import UniqueViolationError

from keyboards import markup
from utils import redis_utils, mobile_utils, weather
from utils.db_api.db_gino import db, Flat, User, BloodPressure, on_startup as gino_on_startup

redis_url = os.getenv("REDISTOGO_URL", "redis://localhost:6379")
telegram_token = os.environ["TELEGRAM_TOKEN"]
weather_token = os.environ["WEATHER_TOKEN"]
database = os.environ["DATABASE_URL"]
delay = int(os.environ["DELAY"])
bp_user = os.environ['BP_USER']

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


@dispatcher.callback_query_handler(text="save_bp_to_db", state=BloodPressureForm.systolic)
async def save_bp_to_db(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        try:
            await BloodPressure.create(**data)
        except UniqueViolationError:
            await call.answer(f'Уже есть показания на {"утро" if data.get("am") else "вечер"} этого дня.')
        else:
            await call.answer(text="Записал.")
    await state.finish()


@dispatcher.callback_query_handler(text="bp_cancel", state=BloodPressureForm.systolic)
async def bp_cancel(call: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await call.answer("отменено и забыто")


@dispatcher.message_handler(Text(equals="❤️"))
async def process_health_worker(message: types.Message, state: FSMContext):
    await types.ChatActions.typing(0.5)
    await BloodPressureForm.date.set()

    async with state.proxy() as data:
        data["date"] = datetime.datetime.now().date()
        data["am"] = datetime.datetime.now().time().hour < 12

    await message.reply("введите показания давление через пробел", reply_markup=markup)


@dispatcher.message_handler(state=BloodPressureForm.date)
async def process_bp(message: types.Message, state: FSMContext):
    input_value = message.text
    systolic, diastolic = input_value.split(" ")

    async with state.proxy() as data:
        data["systolic"] = int(systolic)
        data["diastolic"] = int(diastolic)

    logging.info(data)
    await BloodPressureForm.next()

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="записать показания", callback_data="save_bp_to_db"))
    keyboard.add(types.InlineKeyboardButton(text="отмена", callback_data="bp_cancel"))
    text = f"""{data["date"]} {"🌅" if data["am"] else "😴"}
давление систолическое: {md.code(data["systolic"])}
давление диастолическое: {md.code(data["diastolic"])}
"""
    await message.answer(md.text(text), reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
    await BloodPressureForm.next()


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
async def meter_reading(message: types.Message, state: FSMContext):
    await types.ChatActions.typing(0.5)
    await HomeForm.t.set()

    # previous_data
    last_dt = await db.first(db.text("select date from flat order by date desc LIMIT 1"))
    last_dt = last_dt[0]
    previous_data = await Flat.query.where(Flat.date == last_dt).gino.first()

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["cancel"]
    keyboard.add(*buttons)
    welcome_message = f"""Передача показаний ПУ.\nПоказания на {previous_data.date}
    Т: {previous_data.t}
    Т1: {previous_data.t1}
    Т2: {previous_data.t2}
    холодная: {previous_data.cold}
    горячая: {previous_data.hot}\n
Для прекращения операции - напиши `cancel` или воспользуйся кнопкой `cancel`.\n\nВнеси потребление ⚡ T"""

    async with state.proxy() as data:
        data["previous_t"] = previous_data.t
        data["previous_t1"] = previous_data.t1
        data["previous_t2"] = previous_data.t2
        data["previous_cold"] = previous_data.cold
        data["previous_hot"] = previous_data.hot
        data["previous_date"] = previous_data.date

    await message.reply(welcome_message, reply_markup=keyboard)


@dispatcher.message_handler(Text(equals="cancel", ignore_case=True), state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.finish()
    await types.ChatActions.typing(0.5)
    await message.reply("ОК", reply_markup=markup)


def make_compare_error_message(current: int, previous: int, alarm_value: int = None) -> str:
    if current <= previous:
        return f"""Внесённые показания {'меньше предыдущих' if current < previous else 'идентичны предыдущим'}.
{md.code(previous)}. Повторите ввод."""

    if alarm_value and (current - previous) > alarm_value:
        return f"слишком большая разница между показаниями {current} и {previous}"


@dispatcher.message_handler(lambda message: message.text.isdigit(), state=HomeForm.t)
async def process_t(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.reply("введено не число")

    previous_data = await state.get_data()
    input_value = int(message.text)

    if previous_data:
        previous = previous_data.get("previous_t")

        error_message = make_compare_error_message(current=input_value, previous=previous, alarm_value=300)
        if error_message:
            return await message.reply(error_message)

    async with state.proxy() as data:
        data["t"] = input_value

    await HomeForm.next()
    await message.reply("чудно, а теперь потребление ⚡T1")


@dispatcher.message_handler(lambda message: message.text.isdigit(), state=HomeForm.t1)
async def process_t1(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.reply("введено не число")

    previous_data = await state.get_data()
    input_value = int(message.text)

    if previous_data:
        previous = previous_data.get("previous_t1")

        error_message = make_compare_error_message(current=input_value, previous=previous, alarm_value=50)
        if error_message:
            return await message.reply(error_message)

    await HomeForm.next()
    await state.update_data(t1=input_value)
    await message.reply("чудно, а теперь потребление ⚡T2")


@dispatcher.message_handler(lambda message: message.text.isdigit(), state=HomeForm.t2)
async def process_t2(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.reply("введено не число")

    previous_data = await state.get_data()
    input_value = int(message.text)

    if previous_data:
        previous = previous_data.get("previous_t2")
        error_message = make_compare_error_message(current=input_value, previous=previous, alarm_value=250)
        if error_message:
            return await message.reply(error_message)

    await HomeForm.next()
    await state.update_data(t2=input_value)
    await message.reply("славно, а теперь потребление 🥶🌊")


@dispatcher.message_handler(lambda message: message.text.isdigit(), state=HomeForm.cold)
async def process_cold_water(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.reply("введено не число")

    previous_data = await state.get_data()
    input_value = int(message.text)

    if previous_data:
        previous = previous_data.get("previous_cold")
        error_message = make_compare_error_message(current=input_value, previous=previous, alarm_value=4)
        if error_message:
            return await message.reply(error_message)

    await HomeForm.next()
    await state.update_data(cold=input_value)
    await message.reply("и наконец, внеси потребление 🥵🌊")


@dispatcher.message_handler(lambda message: message.text.isdigit(), state=HomeForm.hot)
async def process_hot_water(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.reply("введено не число")

    previous_data = await state.get_data()
    input_value = int(message.text)

    if previous_data:
        previous = previous_data.get("previous_hot")
        error_message = make_compare_error_message(current=input_value, previous=previous, alarm_value=4)
        if error_message:
            return await message.reply(error_message)

    async with state.proxy() as data:
        data["hot"] = input_value

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="передать показания", callback_data="save_to_db"))

    text = f"""
эл. энергия T: {md.code(data["t"])} diff {md.code(data["t"] - data["previous_t"])}
эл. энергия T1: {md.code(data["t1"])} diff {md.code(data["t1"] - data["previous_t1"])}
эл. энергия T2:{md.code(data["t2"])} diff {md.code(data["t2"] - data["previous_t2"])}
холодная вода: {md.code(data["cold"])} diff {md.code(data["cold"] - data["previous_cold"])}
горячая вода: {md.code(data["hot"])} diff {md.code(data["hot"] - data["previous_hot"])}
проверка t {"❌" if data["t"] - data["t1"] - data["t2"] > 1 else "✔️"}"""

    await message.answer(md.text(text), reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
    await HomeForm.next()


@dispatcher.callback_query_handler(text="save_to_db", state=HomeForm.date)
async def save_to_db(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data["date"] = datetime.datetime.now().date()
        data = dict(filter(lambda item: not item[0].startswith("previous_"), data.items()))
        flat_data = await Flat.get(data["date"])
        if flat_data:
            await flat_data.update(**data).apply()
        else:
            await Flat.create(**data)

    await call.message.answer(f"{data['date'].strftime('%Y %m %d')} saved", reply_markup=markup)
    await state.finish()


def repeat(coro, loop):
    asyncio.ensure_future(coro(), loop=loop)
    loop.call_later(delay, repeat, coro, loop)


async def scheduler():
    while True:
        await schedule.run_pending()
        await asyncio.sleep(1)


async def check_bp():
    if bp_user:
        current_hour = datetime.datetime.now().hour
        if 10 <= current_hour <= 12 or 21 <= current_hour <= 23:
            date = datetime.datetime.now().date()
            am = datetime.datetime.now().time().hour < 12
            some_object = await BloodPressure.get((date, am))
            if some_object is None:
                await bot.send_message(bp_user, f"ёба, а чё, a где?", reply_markup=markup)
            else:
                logging.info(f"we have object: {some_object}")
        logging.info(f"Skip check_bp. Reason: current hour {current_hour}")


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
    loop.call_later(delay, repeat, check_bp, loop)
    asyncio.run(executor.start_polling(dispatcher, on_startup=on_startup, loop=loop, skip_updates=True))
