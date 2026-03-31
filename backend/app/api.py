"""
GPS Shield — API Route Handlers.

All REST API endpoints live here. Mounted on the FastAPI app in main.py.
Currently implements:
    - GET /health: System health check with database status.

Endpoints for zones, stats, findings, and regions will be added in
Steps 13-14.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """
    Return system health status.

    Checks database connectivity and live polling state.
    Used by monitoring, load balancers, and the frontend's
    connection status indicator.

    Returns:
        dict with keys: status, database, live_polling, last_poll, version.
    """
    # Database check will be implemented when we wire up real DB in Step 3.
    # For now, report basic health.
    return {
        "status": "healthy",
        "database": "connected",
        "live_polling": "inactive",
        "last_poll": None,
        "version": "1.0.0",
    }
