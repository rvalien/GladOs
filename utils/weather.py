import logging
import requests

logger = logging.getLogger(__name__)


def get_weather(weather_token: str, city_id: int = 550280) -> str:
    """
    get
    :param weather_token: api token from openweathermap
    :param city_id:  default Khimky Russia
    :return: short weather info in 1 string in celsius
    """
    res = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"id": city_id, "units": "metric", "lang": "ru", "APPID": weather_token},
    )
    data = res.json()
    return f"{round(data['main']['temp'], 1)}C, {data['weather'][0]['description']}"
