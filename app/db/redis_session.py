import redis.asyncio as redis
from app.core.db_config import db_settings

REDIS_URL = f"{'rediss' if db_settings.REDIS_USE_SSL else 'redis'}://{db_settings.REDIS_HOST}:{db_settings.REDIS_PORT}/0"

pool = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)

def get_redis_client() -> redis.Redis:
    return redis.Redis(connection_pool=pool)