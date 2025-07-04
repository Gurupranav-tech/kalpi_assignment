import redis.asyncio as redis
from datetime import datetime
import math

from app.core.settings import settings


redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)


async def limiter(jwt: str, tier: str):
    """
    This is a very basic implementation of rate limiter. We first get the limit for a tier and then see if a entry for the token exists in redis.
    If it exists we see if it any more requests are possible and if possible the current value by one. If it does not exists then we make a new entry for the current token with the value of the limit minus one
    """
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
    # As Premium users have infinite subscription we use float("inf") as the value of the limit for them. Since infinity is not serializable to JSON in python we convert infinity to a string.
    if not math.isfinite(remaining):
        remaining = "infinity"
    return True, remaining
