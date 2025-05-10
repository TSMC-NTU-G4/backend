import json
import os
from typing import TypeVar

import redis
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

# load env variables
load_dotenv()
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
ALERT_SUPPRESS_TIME = int(os.getenv("ALERT_SUPPRESS_TIME"))


# initialize redis connection
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)


def get_alert_suppress_time() -> int:
    # get alert suppress time from cache
    # return default time from env if not found in cache
    time = redis_client.get("ALERT_SUPPRESS_TIME")
    return int(time) if time else ALERT_SUPPRESS_TIME


def get_data_by_prefix(prefix: str, model: type[T]) -> list[T]:
    cursor = 0
    results: list[T] = []

    pattern = f"{prefix}_*"

    while True:
        cursor, keys = redis_client.scan(cursor=cursor, match=pattern, count=100)
        for key in keys:
            raw = redis_client.get(key)
            if raw:
                try:
                    # decode bytes to string if necessary
                    raw_str = raw.decode("utf-8") if isinstance(raw, bytes) else raw
                    results.append(model.model_validate_json(raw_str))
                except (ValidationError, json.JSONDecodeError):
                    continue
        if cursor == 0:
            break

    return results
