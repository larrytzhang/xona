"""
Shared pytest fixtures for GPS Shield backend tests.

Provides:
    - async_client: httpx.AsyncClient wired to the FastAPI test app
    - event_loop: asyncio event loop for async test functions
"""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest.fixture(scope="session")
def event_loop():
    """
    Create a session-scoped event loop for all async tests.

    Returns:
        asyncio.AbstractEventLoop: A new event loop instance.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an httpx AsyncClient connected to the FastAPI test app.

    Yields:
        AsyncClient: Client for making async HTTP requests to the app.
    """
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
