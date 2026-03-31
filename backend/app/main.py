"""
GPS Shield — FastAPI Application Entry Point.

Creates the FastAPI app with:
    - Async lifespan for database connection management.
    - CORS middleware configured from settings.
    - API router mounted at root.

Run with:
    uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifecycle — startup and shutdown.

    On startup:
        - Verify database connectivity.
        - Start live polling task (will be added in Step 12).
    On shutdown:
        - Dispose database engine connections.

    Args:
        app: The FastAPI application instance.

    Yields:
        None — control returns to the app during its runtime.
    """
    # Startup
    from app.database import engine

    # Verify DB is reachable (will fail gracefully if not configured)
    try:
        async with engine.connect() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
    except Exception:
        # DB not available — app still starts, serves cached/mock data
        pass

    yield

    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="GPS Shield",
    description=(
        "Anomaly Detection Engine — analyzes ADS-B aircraft data to detect "
        "GPS spoofing and jamming events, then models how Xona's Pulsar "
        "LEO constellation would neutralize them."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(router)
