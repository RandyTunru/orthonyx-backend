import time
import asyncio
from collections import deque

from fastapi import Header, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.db.session import get_session
from app.crud.user import get_user_by_id
from app.utils.security import decrypt_api_key
from app.schemas.authenticated_user import AuthenticatedUser

async def get_current_user(
    # Use Header to extract values from the request headers
    user_id: str = Header(..., description="The User's unique ID"),
    api_key: str = Header(..., description="The User's API Key"),
    db: AsyncSession = Depends(get_session)
) -> AuthenticatedUser:
   
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

class RateLimiter():
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clients = {}

    async def __call__(self, current_user: AuthenticatedUser = Depends(get_current_user)):
        api_key = current_user.api_key
        current_time = time.time()

        if api_key not in self.clients:
            self.clients[api_key] = {
                "lock": asyncio.Lock(),
                "timestamps": deque() # use deque for efficient pops from left
            }

        client_data = self.clients[api_key]

        # Remove timestamps outside the current window
        async with client_data["lock"]: # ensures only one coroutine modifies timestamps at a time
            while client_data["timestamps"] and client_data["timestamps"][0] <= current_time - self.window_seconds:
                client_data["timestamps"].popleft()

            if len(client_data["timestamps"]) >= self.max_requests:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
            client_data["timestamps"].append(current_time)