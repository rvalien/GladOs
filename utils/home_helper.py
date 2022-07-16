import os
import logging
from typing import Final, NamedTuple
from urllib.parse import urljoin

import aiohttp

URL: Final[str] = "https://lkk.mosobleirc.ru/api/"
CONF_ID = os.environ["MOSOBLEIRC_ID"]


class LkData(NamedTuple):
    password: str
    phone: str


class DataObject(NamedTuple):
    obj_id: int
    obj_type: str
    value: float


class CantGetMetersData(Exception):
    """Program can't get current meters data."""


lk = LkData(
    password=os.environ["MOSOBLEIRC_PASSWORD"],
    phone=os.environ["MOSOBLEIRC_PHONE"],
)


async def get_token(lk_secrets: LkData) -> str | None:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                url=urljoin(URL, "tenants-registration/v2/login"),
                json={
                    "loginMethod": "PERSONAL_OFFICE",
                    "password": lk_secrets.password,
                    "phone": lk_secrets.phone,
                },
            ) as response:
                try:
                    raw_response = await response.json()
                    try:
                        return raw_response["token"]
                    except KeyError:
                        logging.error(raw_response)
                except aiohttp.ContentTypeError as err_text:
                    logging.error(err_text)
                    data = await response.text()
                    raise CantGetMetersData(data)
        except aiohttp.ClientConnectorError as e_text:
            raise CantGetMetersData(e_text)


async def get_data(auth_token: str) -> list | None:
    """Get current data from site."""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url=urljoin(URL, f"api/clients/meters/for-item/{CONF_ID}"),
            headers={"X-Auth-Tenant-Token": auth_token},
        ) as response:
            try:
                return await response.json()
            except aiohttp.ContentTypeError as err_text:
                logging.error(err_text)
                raise CantGetMetersData


async def post_data(auth_token, data_object) -> None:
    """post data
    {"value1": 1034.511}
    {"value1": '44828'}
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=urljoin(URL, f"/clients/meters/{data_object.obj_id}/values"),
            headers={"X-Auth-Tenant-Token": auth_token},
            json={"value1": data_object.value},
        ) as response:
            logging.info(response.status)


def parse_data(raw_list: list) -> str:
    """Prepare text from dict."""
    temp_list = []
    for item in raw_list:
        tmp = item["meter"]
        temp_list.append(f"{tmp['type']}: {tmp['lastValue']['total']['value']} {tmp['lastValue']['settlementPeriod']}")

    return "\n".join(temp_list)


async def previous_data():
    token = await get_token(lk)
    data = await get_data(token)
    return parse_data(data)


async def send_new_data_to_lk(data):
    token = await get_token(lk)
    hw = DataObject(obj_id=1877536, obj_type="HotWater", value=data["hot"])
    cw = DataObject(obj_id=1877537, obj_type="ColdWater", value=data["cold"])
    t = DataObject(obj_id=722791, obj_type="Electricity", value=data["t"])

    await post_data(token, hw)
    await post_data(token, cw)
    await post_data(token, t)
