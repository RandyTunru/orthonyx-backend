import time
import redis.asyncio as redis

from fastapi import Header, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.db.redis_session import get_redis_client
from app.crud.user import get_user_by_id
from app.utils.security import decrypt_api_key
from app.schemas.authenticated_user import AuthenticatedUser

async def get_current_user(
    # Use Header to extract values from the request headers
    user_id: str = Header(..., alias="X-User-ID", description="The User's unique ID"),
    api_key: str = Header(..., alias="X-API-Key", description="The User's API Key"),
    db: AsyncSession = Depends(get_session)
) -> AuthenticatedUser:
    """Dependency to get the current authenticated user based on headers."""
    user = await get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    try:
        raw_api_key = decrypt_api_key(user.api_key_enc)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not process credentials",
        )

    if raw_api_key != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )

    return AuthenticatedUser(id=str(user.id), api_key=api_key)

class RedisTokenBucketRateLimiter:
    """A rate limiter that uses the token bucket algorithm with Redis as the backend."""
    def __init__(self, capacity: int, refill_rate: float, endpoint: str):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.endpoint = endpoint

    async def __call__(self,
                       redis_client: redis.Redis = Depends(get_redis_client),
                       current_user: AuthenticatedUser = Depends(get_current_user)):
        
        user_id = current_user.id
        current_time = time.time()
        key = f"rate_limit:{self.endpoint}:{user_id}"

        # Use a Redis transaction (pipeline) to ensure atomicity
        async with redis_client.pipeline(transaction=True) as pipe:
            pipe.hgetall(key)
            bucket_state = (await pipe.execute())[0]

            tokens = float(bucket_state.get("tokens", self.capacity))
            last_refill_ts = float(bucket_state.get("last_refill_ts", current_time))

            time_elapsed = current_time - last_refill_ts
            tokens_to_add = time_elapsed * self.refill_rate
            
            tokens = min(self.capacity, tokens + tokens_to_add)
            
            if tokens < 1:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
            tokens -= 1

            new_state = {"tokens": tokens, "last_refill_ts": current_time}
            pipe.multi() # Start the transaction block
            pipe.hset(key, mapping=new_state) # Update the user's bucket state
            pipe.expire(key, 60 * 60) # 1 hour expiration
            await pipe.execute()