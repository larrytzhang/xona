"""
GPS Shield — FastAPI Application Entry Point.

Creates the FastAPI app with:
    - Async lifespan for database connection and live polling management.
    - CORS middleware configured from settings.
    - API router mounted at root.
    - Live polling background task for real-time anomaly detection.

Run with:
    uvicorn app.main:app --reload
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api import router
from app.config import settings

logger = logging.getLogger(__name__)

# In-memory cache of live polling state, shared with API endpoints.
live_state = {
    "last_poll": None,
    "poll_status": "inactive",
    "active_zones": [],
    "events_last_hour": 0,
}


async def _live_polling_task() -> None:
    """
    Background task that polls OpenSky for live aircraft state vectors.

    Runs the detection pipeline on each snapshot and updates the
    in-memory cache of active zones. Polls every POLL_INTERVAL_SECONDS.

    This task runs for the lifetime of the FastAPI process and handles
    errors gracefully (logs and retries on next interval).
    """
    from app.detection import AnomalyPipeline
    from app.ingestion import OpenSkyClient
    from app.database import async_session
    from app.models import AnomalyEvent as AnomalyEventModel, InterferenceZone

    client = OpenSkyClient()
    pipeline = AnomalyPipeline()
    interval = settings.POLL_INTERVAL_SECONDS

    live_state["poll_status"] = "active"
    logger.info("Live polling started (interval: %ds)", interval)

    try:
        while True:
            try:
                raw_states = await client.fetch_states()
                now_ts = int(datetime.now(timezone.utc).timestamp())

                if raw_states:
                    events, zones = pipeline.process_snapshot(raw_states, snapshot_time=now_ts)

                    live_state["last_poll"] = datetime.now(timezone.utc)
                    live_state["active_zones"] = zones
                    live_state["events_last_hour"] = len(events)

                    if events or zones:
                        # Store live detections in database.
                        try:
                            async with async_session() as session:
                                for zone in zones:
                                    iz = InterferenceZone(
                                        center_lat=zone.center_lat,
                                        center_lon=zone.center_lon,
                                        radius_km=zone.radius_km,
                                        event_type=zone.event_type,
                                        severity=zone.severity,
                                        affected_aircraft=zone.affected_aircraft,
                                        start_time=zone.start_time,
                                        status="active",
                                        region=zone.region,
                                        is_live=True,
                                        gps_jam_radius_km=zone.gps_jam_radius_km,
                                        pulsar_jam_radius_km=zone.pulsar_jam_radius_km,
                                        spoofing_eliminated=zone.spoofing_eliminated,
                                        signal_advantage_db=zone.signal_advantage_db,
                                        area_reduction_pct=zone.area_reduction_pct,
                                    )
                                    session.add(iz)
                                for event in events:
                                    ac = event.detection.aircraft
                                    ae_flags = [f.model_dump() for f in event.detection.flags]
                                    ae = AnomalyEventModel(
                                        ts=datetime.fromtimestamp(ac.timestamp, tz=timezone.utc),
                                        icao24=ac.icao24,
                                        callsign=ac.callsign or None,
                                        latitude=ac.latitude,
                                        longitude=ac.longitude,
                                        altitude_m=ac.geo_altitude if ac.geo_altitude is not None else ac.baro_altitude,
                                        anomaly_type=event.anomaly_type,
                                        severity=event.severity,
                                        severity_label=event.severity_label,
                                        flags=ae_flags,
                                        region=event.region,
                                        is_live=True,
                                    )
                                    session.add(ae)
                                await session.commit()
                        except Exception:
                            logger.exception("Failed to store live detections")

                    logger.debug(
                        "Poll: %d states, %d anomalies, %d zones",
                        len(raw_states), len(events), len(zones),
                    )
                else:
                    live_state["last_poll"] = datetime.now(timezone.utc)

            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Live polling error — will retry next interval")
                live_state["poll_status"] = "error"

            await asyncio.sleep(interval)

    except asyncio.CancelledError:
        logger.info("Live polling stopped")
    finally:
        await client.close()
        live_state["poll_status"] = "inactive"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifecycle — startup and shutdown.

    On startup:
        - Verify database connectivity.
        - Start live polling background task.
    On shutdown:
        - Cancel live polling task.
        - Dispose database engine connections.

    Args:
        app: The FastAPI application instance.

    Yields:
        None — control returns to the app during its runtime.
    """
    from app.database import engine

    # Verify DB is reachable.
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        logger.warning("Database not available — serving without live data")

    # Start live polling task (if enabled).
    polling_task = None
    if settings.LIVE_POLLING_ENABLED:
        polling_task = asyncio.create_task(_live_polling_task())
    else:
        logger.info("Live polling disabled via LIVE_POLLING_ENABLED=false")

    yield

    # Shutdown: cancel polling and dispose engine.
    if polling_task is not None:
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass
    await engine.dispose()


app = FastAPI(
    title="GPS Shield — Anomaly Detection Engine",
    description=(
        "A research platform that analyzes millions of real ADS-B aircraft "
        "position reports to detect and map GPS spoofing and jamming events "
        "worldwide. Demonstrates how Xona Space Systems' Pulsar LEO "
        "constellation would neutralize each detected threat.\n\n"
        "**Key Features:**\n"
        "- 6 anomaly detectors (velocity, position, altitude, heading, cluster, signal loss)\n"
        "- DBSCAN spatial clustering into interference zones\n"
        "- Pulsar mitigation modeling (6.3x radius reduction, 97.5% area reduction)\n"
        "- Pre-computed key findings across 7 global conflict zones\n"
        "- Live polling of OpenSky Network for real-time detection"
    ),
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Health", "description": "System health and status"},
        {"name": "Zones", "description": "Interference zone data (live + historical)"},
        {"name": "Analytics", "description": "Statistics, findings, and region breakdowns"},
    ],
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["Accept", "Content-Type"],
)

# Mount API routes
app.include_router(router)


# Global exception handler for clean JSON error responses.


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch unhandled exceptions and return a clean JSON error.

    Args:
        request: The incoming request.
        exc: The unhandled exception.

    Returns:
        JSONResponse with 500 status and error detail.
    """
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
