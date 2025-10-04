import pytest_asyncio
import aiohttp

BASE_URL = "http://127.0.0.1:8000"

@pytest_asyncio.fixture
async def api_client():
    """
    Provides an aiohttp.ClientSession for making API requests.
    """
    session = aiohttp.ClientSession(base_url=BASE_URL)
    yield session
    await session.close()