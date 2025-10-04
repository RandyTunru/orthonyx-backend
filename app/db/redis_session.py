import redis.asyncio as redis
from app.core.db_config import db_settings


pool = redis.ConnectionPool.from_url(f"redis://{db_settings.REDIS_HOST}:{db_settings.REDIS_PORT}/0", decode_responses=True)

def get_redis_client() -> redis.Redis:
    return redis.Redis(connection_pool=pool)