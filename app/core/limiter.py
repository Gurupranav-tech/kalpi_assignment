import redis.asyncio as redis
from datetime import datetime
import math

from app.core.settings import settings


redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)


async def limiter(jwt: str, tier: str):
    limit = settings.TIER_CONFIG[tier]["limit"]
    today = datetime.utcnow().strftime("%Y-%m-%d")
    redis_key = f"rate_limit:{jwt}:{today}"

    count = await redis_client.get(redis_key)
    if count is None:
        await redis_client.set(redis_key, 1, ex=86400)
        remaining = limit - 1
        return True, remaining

    if int(count) >= limit:
        return False, 0

    await redis_client.incr(redis_key)
    remaining = limit - int(count) - 1
    if not math.isfinite(remaining):
        remaining = "infinity"
    return True, remaining
