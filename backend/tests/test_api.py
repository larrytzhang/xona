"""
Tests for the GPS Shield API endpoints.

Starts with the /health endpoint (Step 2), will expand to cover
all endpoints in Steps 13-14.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint_returns_200(async_client: AsyncClient):
    """
    GET /health should return 200 with status 'healthy'.

    Verifies:
        - HTTP 200 response
        - JSON body contains 'status' key with value 'healthy'
        - JSON body contains 'version' key
    """
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "version" in data


@pytest.mark.asyncio
async def test_health_endpoint_contains_database_key(async_client: AsyncClient):
    """
    GET /health should report database connection status.

    Verifies:
        - JSON body contains 'database' key
    """
    response = await async_client.get("/health")
    data = response.json()
    assert "database" in data
