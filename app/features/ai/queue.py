from arq import create_pool
from arq.connections import RedisSettings
from app.core.config import settings

async def enqueue_ai_speaking_job(payload: dict):
    redis = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    try:
        # function name must match worker function
        await redis.enqueue_job("ai_score_speaking_job", payload)
    finally:
        redis.close()
        await redis.wait_closed()
