from typing import Optional
from app.config import settings

redis_client = None

async def get_redis():
    global redis_client
    if not settings.redis_enabled:
        return None
    if redis_client is None:
        import redis.asyncio as redis
        redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return redis_client

async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
