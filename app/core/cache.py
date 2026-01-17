from redis.asyncio import Redis
from app.core.config import settings

redis: Redis | None = None

async def init_redis():
    global redis
    # settings.REDIS_URL = "redis://localhost:6379/0"
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)

async def close_redis():
    global redis
    if redis:
        await redis.close()
        redis = None
