"""
This bot made with ❤️
"""

__author__ = "Valien"
__version__ = "2022.2.1"
__maintainer__ = "Valien"
__link__ = "https://github.com/rvalien/GladOs"

import aioschedule as schedule
import asyncio
import datetime
import logging
import os

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import ParseMode
from aiogram.utils import executor, markdown as md
from states import HomeForm, HealthForm
from asyncpg.exceptions import UniqueViolationError

from keyboards import markup
from utils import mobile_utils, weather
from utils.db_api.db_gino import db, Flat, User, Health, on_startup as gino_on_startup

telegram_token = os.environ["TELEGRAM_TOKEN"]
# telegram_token = os.environ["TEST_TELEGRAM_TOKEN"]
weather_token = os.environ["WEATHER_TOKEN"]
database = os.environ["DATABASE_URL"]
delay = int(os.environ["DELAY"])
bp_user = os.environ["BP_USER"]

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


@dispatcher.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    logging.warning("Starting connection.")
    await types.ChatActions.typing(0.5)
    await message.reply("Hello, i'm GladOS. beep boop...\n", reply_markup=markup)


@dispatcher.message_handler(Text(equals="weather"))
async def weather_worker(message):
    await types.ChatActions.typing(0.5)
    await message.reply(await weather.get_weather(weather_token))


@dispatcher.callback_query_handler(text="save_health_to_db", state=HealthForm.weight)
async def save_health_to_db(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        try:
            await Health.create(**data)
        except UniqueViolationError:
            await call.answer("Уже есть показания этого дня. Обновил.")
            obj = await Health.get(data["date"])
            await obj.update(**data).apply()
        await call.answer(text="Записал.")
    await state.finish()


@dispatcher.message_handler(Text(equals=["cancel", "отмена"], ignore_case=True), state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    logging.info("Cancelling state %r", current_state)
    await state.finish()
    await message.reply("Cancelled.", reply_markup=types.ReplyKeyboardRemove())


@dispatcher.message_handler(Text(equals="❤️"))
async def process_health_worker(message: types.Message, state: FSMContext):
    await types.ChatActions.typing(0.5)
    await HealthForm.date.set()

    async with state.proxy() as data:
        data["date"] = datetime.datetime.now().date()
    await message.reply(
        "введите показания через пробел\n*систолическое* *диастолическое* *вес*\n или `cancel` для отмены.",
        reply_markup=markup,
        parse_mode=ParseMode.MARKDOWN,
    )


@dispatcher.message_handler(state=HealthForm.date)
async def process_health(message: types.Message, state: FSMContext):
    input_value = message.text
    systolic, diastolic, weight = input_value.split(" ")

    async with state.proxy() as data:
        data["systolic"] = int(systolic)
        data["diastolic"] = int(diastolic)
        data["weight"] = float(weight.replace(",", "."))
    await HealthForm.last()

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="записать показания", callback_data="save_health_to_db"))
    keyboard.add(types.InlineKeyboardButton(text="отмена", callback_data="cancel_handler"))
    text = f"""{data["date"]}
давление систолическое: {md.code(data["systolic"])}
давление диастолическое: {md.code(data["diastolic"])}
вес: {md.code(data["weight"])}
"""
    await message.answer(md.text(text), reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)


@dispatcher.message_handler(Text(equals="internet"))
async def internet_left_worker(message):
    await types.ChatActions.typing(1)
    user = await User.get(message.from_user.id)
    await message.reply(await mobile_utils.get_internet_limit_text(user))


@dispatcher.message_handler(Text(equals="bill"))
async def get_bill_worker(message):
    await types.ChatActions.typing(1)
    users = await User.query.gino.all()
    await message.reply(await mobile_utils.get_all_bills_text(users))


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


async def check_health():
    if bp_user:
        current_dt = datetime.datetime.now()
        # every three days in morning
        if current_dt.day % 3 == 0 and 10 <= current_dt.hour < 12:
            date = datetime.datetime.now().date()
            some_object = await Health.get(date)
            if some_object is None:
                await bot.send_message(bp_user, "ёба, а чё, a где?", reply_markup=markup)
            else:
                logging.info(f"we have object: {some_object}")


async def on_startup(dispatcher):
    # import filters
    # import middlewares
    # filters.setup(dp)
    # middlewares.setup(dp)
    # from utils.notify_admins import on_startup_notify

    await gino_on_startup(dispatcher)
    # await on_startup_notify(dispatcher)
    asyncio.create_task(scheduler())


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    logging.basicConfig(level=logging.INFO)
    loop.call_later(delay, repeat, check_health, loop)
    asyncio.run(executor.start_polling(dispatcher, on_startup=on_startup, loop=loop, skip_updates=True))
