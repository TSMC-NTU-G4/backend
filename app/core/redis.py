import os

import redis
from dotenv import load_dotenv

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
