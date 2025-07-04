import json
import redis.asyncio as redis

"""
For simplicity we are storing the values as JSON strings in redis database
"""
redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

async def get_cached(key: str):
    data = await redis_client.get(key)
    if data:
        return json.loads(data)
    return None

async def set_cached(key: str, data: dict, ttl: int = 3600):
    await redis_client.set(key, json.dumps(data), ex=ttl)
