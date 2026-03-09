import json
from typing import Any

import redis.asyncio as redis

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

async def get_cache(key: str):
    try:
        value = await redis_client.get(key)
        return value
    except Exception as e:
        print(f"Error getting cache for key {key}: {e}")
        return None

async def get_json_cache(key: str):
    try:
        value = await redis_client.get(key)
        if value is not None:
            return json.loads(value)
        return None
    except Exception as e:
        print(f"Error getting JSON cache for key {key}: {e}")
        return None

async def set_cache(key: str, value: Any, expire: int = 3600):
    try:
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        await redis_client.setex(key, expire, value)
        return True
    except Exception as e:
        print(f"Error setting cache for key {key}: {e}")
        return False