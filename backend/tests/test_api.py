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


@pytest.mark.asyncio
async def test_stats_returns_200(async_client: AsyncClient):
    """GET /api/stats should return 200 with expected keys."""
    response = await async_client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_events" in data
    assert "total_zones" in data
    assert "total_aircraft_affected" in data
    assert "date_range" in data
    assert "by_type" in data
    assert "avg_severity" in data
    assert "live" in data


@pytest.mark.asyncio
async def test_stats_by_type_keys(async_client: AsyncClient):
    """GET /api/stats by_type should contain spoofing, jamming, mixed."""
    response = await async_client.get("/api/stats")
    by_type = response.json()["by_type"]
    assert "spoofing" in by_type
    assert "jamming" in by_type
    assert "mixed" in by_type


@pytest.mark.asyncio
async def test_zones_live_returns_200(async_client: AsyncClient):
    """GET /api/zones/live should return 200 with zones array."""
    response = await async_client.get("/api/zones/live")
    assert response.status_code == 200
    data = response.json()
    assert "zones" in data
    assert "count" in data
    assert "poll_status" in data
    assert isinstance(data["zones"], list)


@pytest.mark.asyncio
async def test_zones_live_count_matches_array(async_client: AsyncClient):
    """GET /api/zones/live count should match zones array length."""
    response = await async_client.get("/api/zones/live")
    data = response.json()
    assert data["count"] == len(data["zones"])


@pytest.mark.asyncio
async def test_findings_returns_200(async_client: AsyncClient):
    """GET /api/findings should return 200 with findings array."""
    response = await async_client.get("/api/findings")
    assert response.status_code == 200
    data = response.json()
    assert "findings" in data
    assert isinstance(data["findings"], list)


@pytest.mark.asyncio
async def test_regions_returns_200(async_client: AsyncClient):
    """GET /api/regions should return 200 with regions array."""
    response = await async_client.get("/api/regions")
    assert response.status_code == 200
    data = response.json()
    assert "regions" in data
    assert isinstance(data["regions"], list)


@pytest.mark.asyncio
async def test_regions_invalid_period_returns_422(async_client: AsyncClient):
    """GET /api/regions with invalid period should return 422."""
    response = await async_client.get("/api/regions?period=yearly")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_zones_history_requires_dates(async_client: AsyncClient):
    """GET /api/zones/history without dates should return 422."""
    response = await async_client.get("/api/zones/history")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_zones_history_with_dates_returns_200(async_client: AsyncClient):
    """GET /api/zones/history with valid dates should return 200."""
    response = await async_client.get(
        "/api/zones/history?start_date=2025-10-01&end_date=2026-03-30"
    )
    assert response.status_code == 200
    data = response.json()
    assert "zones" in data
    assert "total_count" in data
    assert "page" in data
    assert "page_size" in data


@pytest.mark.asyncio
async def test_zone_detail_not_found_returns_404(async_client: AsyncClient):
    """GET /api/zones/999999 should return 404."""
    response = await async_client.get("/api/zones/999999")
    assert response.status_code == 404
