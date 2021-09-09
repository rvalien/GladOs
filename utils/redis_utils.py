import datetime
import logging

from itertools import product

logger = logging.getLogger(__name__)


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


def usage_log(users, redis_client) -> str:
    result = ""
    for user, command in product(users, ("work", "rest")):
        user_id = f"{user}_{command}"
        interacts = redis_client.get(f"{user_id}_interacts").decode() if redis_client.get(f"{user_id}_interacts") else 0
        last_interact_ts = redis_client.get(f"{user_id}_last_interact_timestamp")
        if last_interact_ts:
            last_interact_ts = last_interact_ts.decode()
            last_interact_ts = datetime.datetime.fromtimestamp(float(last_interact_ts)).strftime("%Y-%m-%d %H:%M:%S")
        result += f"{user_id}:\n {interacts=}\n{last_interact_ts=}\n\n"

    return result
