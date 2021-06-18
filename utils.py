# -*- coding: utf-8 -*-
import requests


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


def get_ststel_data(login: str, password: str) -> dict:
    """

    :param login:
    :param password:
    :return:
    """
    url = "https://ststel.ru/lk/submit.php"
    header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0"}
    payload = {"phone": str(login), "pass": str(password)}
    a, b, i = 0, 0, 0
    with requests.Session() as s:
        # we need while because ststel returns zeroes some times
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
        result[item[0]] = get_ststel_data(**item)
    return result


def print_ststel_info(data: dict) -> str:
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
        balans = data["balance"]
    else:
        balans = data["balance"], data["effectiveBalance"]

    return f"""Осталось {internet} {i}. Баланс: {balans} р. """


def free_time(message, redis_client) -> str:
    """
    commands (all, clean)
    :return: short string
    """

    user_id = message.from_user.id
    param = message.text.split("/time ")

    if param == ["/time"]:
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
