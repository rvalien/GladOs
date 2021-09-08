import asyncio
import datetime
import logging
import os
import psycopg2
import redis

# import pika
from states import HomeForm
from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import ParseMode
from aiogram.utils import executor, markdown as md

from utils import get_weather, get_mobile_data, print_mobile_info, rest_time, work_time, usage_log
from keyboards import markup

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

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
dp = Dispatcher(bot, storage=storage)

conn = psycopg2.connect(database)
cursor = conn.cursor()
CLIENT = redis.from_url(redis_url)

cursor.execute("select chat_id from users")
chat_ids = list(map(lambda x: x[0], cursor.fetchall()))
logger.info(chat_ids)


@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    await types.ChatActions.typing(0.5)
    await message.reply("Hello, i'm GladOS. beep boop...\n", reply_markup=markup)


@dp.message_handler(Text(equals="weather"))
async def weather_worker(message):
    await types.ChatActions.typing(0.5)
    await message.reply(get_weather(weather_token))


@dp.message_handler(commands=["rest"])
async def free_time_worker(message):
    await types.ChatActions.typing(0.5)
    await message.reply(rest_time(message, CLIENT))


@dp.message_handler(commands=["work"])
async def work_time_worker(message):
    await types.ChatActions.typing(0.5)
    await message.reply(work_time(message, CLIENT))


@dp.message_handler(Text(equals="internet"))
async def internet_left_worker(message):
    await types.ChatActions.typing(0.5)
    conn = psycopg2.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"select phone, password from users where chat_id = {message['from']['id']}")
    res = cursor.fetchone()
    await message.reply(str(print_mobile_info(get_mobile_data(*res))))


@dp.message_handler(Text(equals="bill"))
async def get_bill_worker(message):
    await types.ChatActions.typing(0.5)
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
    await types.ChatActions.typing(0.5)
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
    await types.ChatActions.typing(0.5)
    await message.reply(message.from_user)


@dp.message_handler(Text(equals="🏡"))
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


@dp.message_handler(Text(equals="cancel", ignore_case=True), state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.finish()
    await types.ChatActions.typing(0.5)
    await message.reply("ОК", reply_markup=markup)


@dp.message_handler(lambda message: message.text.isdigit(), state=HomeForm.t)
async def process_t(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.reply("введено не число")

    async with state.proxy() as data:
        data["t"] = int(message.text)

    await HomeForm.next()
    await message.reply("чудно, а теперь потребление ⚡T1")


@dp.message_handler(lambda message: message.text.isdigit(), state=HomeForm.t1)
async def process_t1(message: types.Message, state: FSMContext):
    await HomeForm.next()
    await state.update_data(t1=int(message.text))
    await message.reply("чудно, а теперь потребление ⚡T2")


@dp.message_handler(lambda message: message.text.isdigit(), state=HomeForm.t2)
async def process_t2(message: types.Message, state: FSMContext):
    await HomeForm.next()
    await state.update_data(t2=int(message.text))
    await message.reply("славно, а теперь потребление 🥶🌊")


@dp.message_handler(lambda message: message.text.isdigit(), state=HomeForm.cw)
async def process_cw(message: types.Message, state: FSMContext):
    await HomeForm.next()
    await state.update_data(cw=int(message.text))
    await message.reply("и наконец, внеси потребление 🥵🌊")


@dp.message_handler(lambda message: message.text.isdigit(), state=HomeForm.hw)
async def process_hw(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["hw"] = int(message.text)

    now = datetime.datetime.now().date()
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="передать показания", callback_data="save_to_db"))
    await message.answer(
        md.text(
            md.bold(f"показания на {now.strftime('%Y %m %d')}"),
            md.text("электроэнергия T:", md.code(data["t"])),
            md.text("электроэнергия T1:", md.code(data["t1"])),
            md.text("электроэнергия T2:", md.code(data["t2"])),
            md.text("холодная вода:", md.code(data["cw"])),
            md.text("горячая вода:", md.code(data["hw"])),
            sep="\n",
        ),
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )
    await HomeForm.next()


@dp.callback_query_handler(text="save_to_db", state=HomeForm.fin)
async def save_to_db(call: types.CallbackQuery, state: FSMContext):
    logger.info(await state.get_data())

    async with state.proxy() as data:
        query = f"""
        insert into flat (t, t1, t2, cold, hot, "date")
        values ({data["t"]}, {data["t1"]}, {data["t2"]}, {data["cw"]}, {data["hw"]}, current_date);
        """
    logger.info(query)

    with psycopg2.connect(database) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)

    await call.message.answer("saved", reply_markup=markup)
    await call.answer(text="Спасибо, что воспользовались ботом!")
    await state.finish()


def repeat(coro, loop):
    asyncio.ensure_future(coro(), loop=loop)
    loop.call_later(delay, repeat, coro, loop)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    # loop.call_later(delay, repeat, some_task, loop)
    asyncio.run(executor.start_polling(dp, loop=loop))
