import json
import os
from datetime import datetime
from typing import NamedTuple

import aiohttp
from utils.db_api.db_gino import User

from exceptions import CantGetPhoneData

mobile_lk_url = os.environ["MOBILE_LK_URL"]

Bytes = int


class PhoneData(NamedTuple):
    ctn: str
    plan: str
    balance: float
    effectiveBalance: float
    blcokDate: datetime.date
    unblockable: bool
    rest_voice_initial: int
    rest_voice_current: int
    rest_voice_used: int
    rest_sms_initial: int
    rest_sms_current: int
    rest_sms_used: int
    rest_internet_initial: Bytes
    rest_internet_current: Bytes
    rest_internet_used: Bytes


async def get_mobile_data(user: User) -> PhoneData:
    """
    :param user:
    :return: PhoneData
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(url=mobile_lk_url, data={"phone": user.phone, "pass": user.password}) as response:
            raw_response = await response.text()

            if response.status == 200:
                raw_response = json.loads(raw_response).get("customers", [])[0].get("ctnInfo")
                raw_response["blcokDate"] = datetime.strptime(raw_response["blcokDate"], "%Y-%m-%d").date()
                return PhoneData(**raw_response)
            else:
                raise CantGetPhoneData(raw_response)


def print_mobile_info(data: PhoneData) -> str:
    """
    :param data: data from
    :return: short string

    example:
        Осталось 19.58 Gb. Баланс: 1.49 р.
    """
    gb = 1024
    val = data.rest_internet_current if data.rest_internet_current <= gb else round(data.rest_internet_current / gb, 2)
    i = "Mb" if data.rest_internet_current <= gb else "Gb"
    return f"Осталось {val} {i}. Баланс: {data.balance} р."


async def get_all_mobile_bills(all_users: list[User, ...]) -> dict[str, PhoneData]:
    result = {}
    for user in all_users:
        user_data = await get_mobile_data(user)
        result[user.name] = user_data
    return result


def prepare_response_text(data: dict[str, PhoneData]) -> str:
    """
    example:
        Username0: 1.49
        Username1: 1.5
        username2: 2363.72
        modem: -2.63
    """
    temp_list = []
    for key, phone_data in data.items():
        temp = f"{key}: {phone_data.balance} р."
        temp_list.append(temp)
    return "\n".join(temp_list)


async def get_internet_limit_text(user: User) -> str:
    """`internet` Action function, to get user's internet data."""
    data = await get_mobile_data(user)
    return print_mobile_info(data)


async def get_all_bills_text(users: list[User]):
    """`bill` Action function, to get all balances."""

    data = await get_all_mobile_bills(users)
    return prepare_response_text(data)
