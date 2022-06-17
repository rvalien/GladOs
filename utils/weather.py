import logging
import aiohttp

from exceptions import ApiServiceError

logger = logging.getLogger(__name__)


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
