import logging
import os

import aiohttp
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from exceptions import ApiServiceError

logger = logging.getLogger(__name__)

WEATHER_TOKEN = os.environ["WEATHER_TOKEN"]


async def get_weather(weather_token: str, city_id: int = 550280) -> str:
    """
    get
    :param weather_token: api token from openweathermap
    :param city_id:  default Khimky Russia
    :return: short weather info in 1 string in celsius
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
                url="https://api.openweathermap.org/data/2.5/weather",
                params={"id": city_id, "units": "metric", "lang": "ru", "APPID": weather_token},
        ) as response:
            try:
                data = await response.json()
            except ValueError as err_text:
                raise ApiServiceError(err_text)
    return f"{round(data['main']['temp'], 1)}C, {data['weather'][0]['description']}"


router = Router()


@router.message(Command("weather"))
async def weather_handler(message: Message):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    weather_info = await get_weather(WEATHER_TOKEN)
    await message.reply(weather_info)
