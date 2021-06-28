import asyncio
import logging
import os
import psycopg2
import redis

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
from utils import get_weather, get_mobile_data, print_mobile_info, rest_time, work_time, free_time_log

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


redis_url = os.getenv("REDISTOGO_URL", "redis://localhost:6379")
telegram_token = os.environ["TELEGRAM_TOKEN"]
weather_token = os.environ["WEATHER_TOKEN"]
database = os.environ["DATABASE_URL"]
delay = int(os.environ["DELAY"])

bot = Bot(token=telegram_token)
dp = Dispatcher(bot)

conn = psycopg2.connect(database)
cursor = conn.cursor()

CLIENT = redis.from_url(redis_url)

cursor.execute("select chat_id from users")
chat_ids = list(map(lambda x: x[0], cursor.fetchall()))
logger.info(chat_ids)

markup = ReplyKeyboardMarkup()
markup.row(KeyboardButton("/work"), KeyboardButton("/rest"))
markup.row(KeyboardButton("weather"), KeyboardButton("internet"), KeyboardButton("bill"))


@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    await types.ChatActions.typing(1)
    await message.reply(
        "Hello, i'm GladOS. beep boop...\n", reply_markup=markup
    )


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
    await message.reply(free_time_log(users, CLIENT))


@dp.message_handler(commands=["myid"])
async def debug_worker(message):
    await types.ChatActions.typing(2)
    await message.reply(message.from_user)


def repeat(coro, loop):
    asyncio.ensure_future(coro(), loop=loop)
    loop.call_later(delay, repeat, coro, loop)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    # loop.call_later(delay, repeat, some_task, loop)
    asyncio.run(executor.start_polling(dp, loop=loop))
