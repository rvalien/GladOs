import os
import requests

mobile_lk_url = os.environ["MOBILE_LK_URL"]


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
        # we need while because provider returns zeroes sometimes
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


def get_all_mobile_bills(all_users):
    result = dict()
    for user in all_users:
        result[user.name] = get_mobile_data(login=user.phone, password=user.password)
    return result


def prepare_response_text(data):
    temp_list = list()
    for key in data.keys():
        temp = f'{key}: {data[key].get("effectiveBalance") if data[key].get("effectiveBalance") else data[key].get("balance")}'
        temp_list.append(temp)
    return "\n".join(temp_list)


def get_internet_limit_text(user):
    return print_mobile_info(get_mobile_data(user.phone, user.password))


def get_all_bills_text(users):
    return prepare_response_text(get_all_mobile_bills(users))
