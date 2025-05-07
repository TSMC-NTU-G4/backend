import os

import redis
from dotenv import load_dotenv

# load env variables
load_dotenv()
REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = os.environ.get("REDIS_PORT")

# initialize redis connection
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
