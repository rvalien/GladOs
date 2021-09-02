import asyncio
import datetime
import logging
import os
import psycopg2
import redis
# import pika

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ParseMode
from aiogram.utils import executor, markdown as md
from utils import get_weather, get_mobile_data, print_mobile_info, rest_time, work_time, usage_log

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

redis_url = os.getenv("REDISTOGO_URL", "redis://localhost:6379")
telegram_token = os.environ["TELEGRAM_TOKEN"]
weather_token = os.environ["WEATHER_TOKEN"]
database = os.environ["DATABASE_URL"]
delay = int(os.environ["DELAY"])

bot = Bot(token=telegram_token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

conn = psycopg2.connect(database)
cursor = conn.cursor()

CLIENT = redis.from_url(redis_url)

cursor.execute("select chat_id from users")
chat_ids = list(map(lambda x: x[0], cursor.fetchall()))
logger.info(chat_ids)

markup = ReplyKeyboardMarkup()
markup.row(KeyboardButton("/led_on"), KeyboardButton("/led_off"))
markup.row(KeyboardButton("/work"), KeyboardButton("/rest"), KeyboardButton("🏡"))
markup.row(KeyboardButton("weather"), KeyboardButton("internet"), KeyboardButton("bill"))


@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    await types.ChatActions.typing(1)
    await message.reply("Hello, i'm GladOS. beep boop...\n", reply_markup=markup)


@dp.message_handler(Text(equals="weather"))
async def weather_worker(message):
    await types.ChatActions.typing(1)
    await message.reply(get_weather(weather_token))


@dp.message_handler(commands=["rest"])
async def free_time_worker(message):
    await types.ChatActions.typing(1)
    await message.reply(rest_time(message, CLIENT))


@dp.message_handler(commands=["work"])
async def work_time_worker(message):
    await types.ChatActions.typing(1)
    await message.reply(work_time(message, CLIENT))


@dp.message_handler(Text(equals="internet"))
async def internet_left_worker(message):
    await types.ChatActions.typing(2)
    conn = psycopg2.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"select phone, password from users where chat_id = {message['from']['id']}")
    res = cursor.fetchone()
    await message.reply(str(print_mobile_info(get_mobile_data(*res))))


@dp.message_handler(Text(equals="bill"))
async def get_bill_worker(message):
    await types.ChatActions.typing(2)
    conn = psycopg2.connect(database)
    cursor = conn.cursor()
    cursor.execute("select phone, password, name from users")
    res = cursor.fetchall()

    def get_all_mobile_bills(all_users):
        result = dict()
        for user in all_users:
            result[user[2]] = get_mobile_data(login=user[0], password=user[1])
        return result

    def _prepare_response_text(data):
        temp_list = list()
        for key in data.keys():
            temp = f'{key}: {data[key].get("effectiveBalance") if data[key].get("effectiveBalance") else data[key].get("balance")}'
            temp_list.append(temp)
        return "\n".join(temp_list)

    await message.reply(_prepare_response_text(get_all_mobile_bills(res)))


@dp.message_handler(commands=["log"])
async def get_free_time_log_worker(message):
    await types.ChatActions.typing(2)
    conn = psycopg2.connect(database)
    cursor = conn.cursor()
    cursor.execute("select chat_id from users")
    users = list(map(lambda x: x[0], cursor.fetchall()))
    logger.info("=" * 30)
    logger.info(users)
    logger.info("=" * 30)
    await message.reply(usage_log(users, CLIENT))


@dp.message_handler(commands=["myid"])
async def debug_worker(message):
    await types.ChatActions.typing(2)
    await message.reply(message.from_user)


class Form(StatesGroup):
    t = State()
    t1 = State()
    t2 = State()
    cw = State()
    hw = State()
    valid = State()


@dp.message_handler(Text(equals="🏡"))
async def meter_reading(message: types.Message):
    await Form.t.set()
    await types.ChatActions.typing(.2)
    await message.reply("внеси потребление ⚡ T")


@dp.message_handler(state="*", commands="cancel")
@dp.message_handler(Text(equals="отмена", ignore_case=True), state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.finish()
    await types.ChatActions.typing(.2)
    await message.reply("ОК")


@dp.message_handler(state=Form.t)
async def process_t(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["t"] = message.text

    await Form.next()
    await types.ChatActions.typing(.2)
    await message.reply("чудно, а теперь внеси потребление ⚡T1️⃣")


@dp.message_handler(lambda message: message.text.isdigit(), state=Form.t1)
async def process_t1(message: types.Message, state: FSMContext):
    await Form.next()
    await state.update_data(t1=int(message.text))
    await types.ChatActions.typing(.2)
    await message.reply("чудно, а теперь внеси потребление ⚡T2️⃣")


@dp.message_handler(lambda message: message.text.isdigit(), state=Form.t2)
async def process_t2(message: types.Message, state: FSMContext):
    await Form.next()
    await state.update_data(t2=int(message.text))
    await types.ChatActions.typing(.2)
    await message.reply("славно, а теперь потребление 🥶🌊")


@dp.message_handler(lambda message: message.text.isdigit(), state=Form.cw)
async def process_cw(message: types.Message, state: FSMContext):
    await Form.next()
    await state.update_data(cw=int(message.text))
    await types.ChatActions.typing(.2)
    await message.reply("и наконец, внеси потребление 🥵🌊")


@dp.message_handler(state=Form.hw)
async def process_hw(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["hw"] = message.text
        now = datetime.datetime.now().date()
        logger.info(now)
        logger.info(data)
        query = f"""
        insert into flat (t, t1, t2, cold, hot, "date")
        values ({data["t"]}, {data["t1"]}, {data["t2"]}, {data["cw"]}, {data["hw"]}, current_date);"""

        with psycopg2.connect(database) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)

        await types.ChatActions.typing(.2)
        await bot.send_message(
            message.chat.id,
            md.text(
                md.bold(f"сохранены показания на {now.strftime('%Y %m %d')}"),
                md.text("электроэнергия T:", md.code(data["t"])),
                md.text("электроэнергия T1:", md.code(data["t1"])),
                md.text("электроэнергия T2:", md.code(data["t2"])),
                md.text("холодная вода:", md.code(data["cw"])),
                md.text("горячая вода:", md.code(data["hw"])),
                sep="\n",
            ),
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN,
        )

        await state.finish()


def repeat(coro, loop):
    asyncio.ensure_future(coro(), loop=loop)
    loop.call_later(delay, repeat, coro, loop)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    # loop.call_later(delay, repeat, some_task, loop)
    asyncio.run(executor.start_polling(dp, loop=loop))
