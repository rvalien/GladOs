# -*- coding: utf-8 -*-
import datetime
import logging
import os
import requests

logger = logging.getLogger(__name__)

mobile_lk_url = os.environ["MOBILE_LK_URL"]


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


def get_mobile_data(login: str, password: str) -> dict:
    """

    :param login:
    :param password:
    :return:
    """
    url = mobile_lk_url
    header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0"}
    payload = {"phone": str(login), "pass": str(password)}
    a, b, i = 0, 0, 0
    with requests.Session() as s:
        # we need while because provider returns zeroes some times
        while a == 0 and b == 0:
            r = s.post(url, data=payload, headers=header)
            if r.status_code != 200:
                return {"error": f"ошибка авторизации {r.status_code} {r.text}"}
            else:
                foo = r.json()["customers"]
                if len(foo) != 1:
                    print(f"error: {foo=}, {len(foo)=}")
                else:
                    foo = foo[0]
                    a, b = foo["ctnInfo"]["balance"], foo["ctnInfo"]["rest_internet_current"]
                i += 1
        return foo["ctnInfo"]


def get_all_mobile_bills(all_users):
    result = dict()
    for item in all_users:
        result[item[0]] = get_mobile_data(**item)
    return result


def print_mobile_info(data: dict) -> str:
    """

    :param data: data from
    :return: short string
    """
    internet = int(data["rest_internet_current"])

    if internet >= 1024:
        i = "Gb"
        internet = round(internet / 1024, 2)
    else:
        i = "Mb"

    if int(data["balance"]) != int(data["effectiveBalance"]):
        balance = data["balance"]
    else:
        balance = data["balance"], data["effectiveBalance"]

    return f"""Осталось {internet} {i}. Баланс: {balance} р. """


def rest_time(message, redis_client) -> str:
    """
    commands (all, clean)
    :return: short string
    """

    user_id = f"{message.from_user.id}_rest"
    utc_now = datetime.datetime.utcnow()
    param = message.text.split("/rest ")
    interacts = redis_client.get(f"{user_id}_interacts") if redis_client.get(f"{user_id}_interacts") else 0
    interacts_update = redis_client.set(f"{user_id}_interacts", int(interacts) + 1)
    redis_client.set(f"{user_id}_last_interact_timestamp", utc_now.timestamp())
    logger.info(f"{user_id=}\n{utc_now.strftime('%Y-%m-%d %H:%M:%S')}\n{param=}\n{interacts=}\n{interacts_update=}")

    if param == ["/rest"]:
        random_element_from_set = redis_client.srandmember(user_id)
        if random_element_from_set:
            return random_element_from_set.decode()
        else:
            return "nothing in your list"
    else:
        if param[-1] == "all":
            set_elements = redis_client.smembers(user_id)
            return f"all list:\n {', '.join(map(bytes.decode, set_elements))}"

        elif param[-1] == "clean":
            redis_client.delete(user_id)
            return "clean done"

        else:
            data_to_add = param[-1].casefold().split(", ")

            add_result = redis_client.sadd(user_id, *data_to_add)
            if add_result == 1:
                return "add some."
            else:
                return f"{data_to_add} already in your list."


def work_time(message, redis_client) -> str:
    """
    commands (all, clean)
    :return: short string
    """

    user_id = f"{message.from_user.id}_work"
    utc_now = datetime.datetime.utcnow()
    param = message.text.split("/work ")
    interacts = redis_client.get(f"{user_id}_interacts") if redis_client.get(f"{user_id}_interacts") else 0
    interacts_update = redis_client.set(f"{user_id}_interacts", int(interacts) + 1)
    redis_client.set(f"{user_id}_last_work_interact_timestamp", utc_now.timestamp())
    logger.info(f"{user_id=}\n{utc_now.strftime('%Y-%m-%d %H:%M:%S')}\n{param=}\n{interacts=}\n{interacts_update=}")

    if param == ["/work"]:
        random_element_from_set = redis_client.srandmember(user_id)
        if random_element_from_set:
            return random_element_from_set.decode()
        else:
            return "nothing in your list"
    else:
        if param[-1] == "all":
            set_elements = redis_client.smembers(user_id)
            return f"all list:\n {', '.join(map(bytes.decode, set_elements))}"

        elif param[-1] == "clean":
            redis_client.delete(user_id)
            return "clean done"

        else:
            data_to_add = param[-1].casefold().split(", ")

            add_result = redis_client.sadd(user_id, *data_to_add)
            if add_result == 1:
                return "add some."
            else:
                return f"{data_to_add} already in your list."


def rest_time_log(users, redis_client) -> str:
    result = ""
    for user_id in users:
        user_id = f"{user_id}_rest"
        interacts = redis_client.get(f"{user_id}_interacts").decode() if redis_client.get(f"{user_id}_interacts") else 0
        last_interact_ts = redis_client.get(f"{user_id}_last_interact_timestamp")
        if last_interact_ts:
            last_interact_ts = last_interact_ts.decode()
            last_interact_ts = datetime.datetime.fromtimestamp(float(last_interact_ts)).strftime("%Y-%m-%d %H:%M:%S")
        result += f"{user_id}:\n {interacts=}\n{last_interact_ts=}\n\n"

    return result
