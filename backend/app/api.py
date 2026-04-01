"""
GPS Shield — API Route Handlers.

All REST API endpoints for the GPS Shield platform. Matches the
contracts defined in Part 6 of the master plan exactly.

Security:
    - All endpoints are rate-limited via slowapi (configurable via RATE_LIMIT).
    - Input validation enforces bounds on pagination, date ranges, and enums.
    - All queries use parameterized SQLAlchemy — no SQL injection risk.

Endpoints:
    GET /health              — System health check.
    GET /api/zones/live      — Active interference zones.
    GET /api/zones/history   — Historical zones with filters.
    GET /api/zones/{zone_id} — Zone detail with events.
    GET /api/stats           — Global dashboard statistics.
    GET /api/findings        — Pre-computed key findings.
    GET /api/regions         — Per-region breakdowns with trends.
"""

from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select, text

from app.database import async_session
from app.models import AnomalyEvent, Finding, InterferenceZone, RegionStat
from app.schemas import (
    FindingsResponse,
    HealthResponse,
    RegionsResponse,
    StatsResponse,
    ZoneDetailResponse,
    ZonesHistoryResponse,
    ZonesLiveResponse,
)

router = APIRouter()

# Valid region identifiers — reject anything else.
VALID_REGIONS = frozenset({
    "baltic_sea", "eastern_med", "persian_gulf", "red_sea",
    "black_sea", "ukraine_frontline", "south_china_sea", "other",
})

# Maximum date range span to prevent full-table scans.
MAX_DATE_RANGE_DAYS = 365


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@router.get("/health", response_model=HealthResponse)
async def health_check() -> dict:
    """
    Return system health status.

    Checks database connectivity and live polling state. Used by
    monitoring, load balancers, and the frontend status indicator.
    """
    from app.main import live_state

    db_status = "disconnected"
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        pass

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "live_polling": live_state.get("poll_status", "inactive"),
        "last_poll": live_state.get("last_poll"),
        "version": "1.0.0",
    }


# ---------------------------------------------------------------------------
# Zones
# ---------------------------------------------------------------------------


def _zone_to_response(zone: InterferenceZone) -> dict:
    """Convert an InterferenceZone ORM model to a response dict."""
    return {
        "id": zone.id,
        "center_lat": zone.center_lat,
        "center_lon": zone.center_lon,
        "radius_km": zone.radius_km,
        "event_type": zone.event_type,
        "severity": zone.severity,
        "affected_aircraft": zone.affected_aircraft,
        "start_time": zone.start_time,
        "end_time": zone.end_time,
        "status": zone.status,
        "region": zone.region,
        "is_live": zone.is_live,
        "gps_jam_radius_km": zone.gps_jam_radius_km,
        "pulsar_jam_radius_km": zone.pulsar_jam_radius_km,
        "spoofing_eliminated": zone.spoofing_eliminated,
        "signal_advantage_db": zone.signal_advantage_db,
        "area_reduction_pct": zone.area_reduction_pct,
    }


@router.get("/api/zones/live", response_model=ZonesLiveResponse)
async def get_zones_live(
    hours_back: int = Query(default=24, ge=1, le=168, description="Hours to look back"),
) -> dict:
    """
    Get currently active interference zones.

    Returns zones detected within the last `hours_back` hours,
    prioritizing live-detected zones. Falls back to most recent
    historical data when no live zones exist.
    """
    from app.main import live_state

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)

    async with async_session() as session:
        result = await session.execute(
            select(InterferenceZone)
            .where(InterferenceZone.start_time >= cutoff)
            .order_by(InterferenceZone.start_time.desc())
            .limit(200)
        )
        zones = result.scalars().all()

        # Fallback: if no recent zones, show the most recent historical zones
        # so the globe is never empty when seed data exists.
        if not zones:
            result = await session.execute(
                select(InterferenceZone)
                .order_by(InterferenceZone.start_time.desc())
                .limit(200)
            )
            zones = result.scalars().all()

    zone_responses = [_zone_to_response(z) for z in zones]

    return {
        "count": len(zone_responses),
        "last_poll": live_state.get("last_poll"),
        "poll_status": live_state.get("poll_status", "inactive"),
        "zones": zone_responses,
    }


@router.get("/api/zones/history", response_model=ZonesHistoryResponse)
async def get_zones_history(
    start_date: str = Query(..., description="Start date (ISO format, e.g. 2025-10-01)"),
    end_date: str = Query(..., description="End date (ISO format, e.g. 2026-03-30)"),
    region: Optional[str] = Query(default=None, description="Filter by region slug"),
    event_type: Optional[Literal["spoofing", "jamming", "mixed"]] = Query(default=None, description="spoofing, jamming, or mixed"),
    min_severity: Optional[int] = Query(default=None, ge=0, le=100, description="Minimum severity (0-100)"),
    page: int = Query(default=1, ge=1, le=10000, description="Page number (max 10000)"),
    page_size: int = Query(default=50, ge=1, le=100, description="Results per page (max 100)"),
) -> dict:
    """
    Get historical interference zones with filters and pagination.

    Input validation:
        - Dates must be valid ISO format.
        - Date range cannot exceed 365 days (prevents full-table scans).
        - Region must be a known identifier if provided.
        - Page capped at 10,000; page_size capped at 100.
    """
    # Parse and validate dates.
    try:
        start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        end = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format. Use ISO format (YYYY-MM-DD).")

    if end < start:
        raise HTTPException(status_code=422, detail="end_date must be after start_date.")

    if (end - start).days > MAX_DATE_RANGE_DAYS:
        raise HTTPException(
            status_code=422,
            detail=f"Date range cannot exceed {MAX_DATE_RANGE_DAYS} days.",
        )

    # Validate region if provided.
    if region and region not in VALID_REGIONS:
        raise HTTPException(status_code=422, detail=f"Unknown region: {region}")

    query = select(InterferenceZone).where(
        InterferenceZone.start_time >= start,
        InterferenceZone.start_time <= end,
    )
    count_query = select(func.count(InterferenceZone.id)).where(
        InterferenceZone.start_time >= start,
        InterferenceZone.start_time <= end,
    )

    if region:
        query = query.where(InterferenceZone.region == region)
        count_query = count_query.where(InterferenceZone.region == region)
    if event_type:
        query = query.where(InterferenceZone.event_type == event_type)
        count_query = count_query.where(InterferenceZone.event_type == event_type)
    if min_severity is not None:
        query = query.where(InterferenceZone.severity >= min_severity)
        count_query = count_query.where(InterferenceZone.severity >= min_severity)

    async with async_session() as session:
        result = await session.execute(count_query)
        total_count = result.scalar() or 0

        offset = (page - 1) * page_size
        result = await session.execute(
            query.order_by(InterferenceZone.start_time.desc())
            .offset(offset)
            .limit(page_size)
        )
        zones = result.scalars().all()

    return {
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "zones": [_zone_to_response(z) for z in zones],
    }


@router.get("/api/zones/{zone_id}", response_model=ZoneDetailResponse)
async def get_zone_detail(zone_id: int) -> dict:
    """
    Get detailed view of a single zone with its aircraft events.

    Returns 404 if zone_id does not exist. Events capped at 100.
    """
    # Reject obviously invalid IDs without hitting DB.
    if zone_id < 1 or zone_id > 2_147_483_647:
        raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found")

    async with async_session() as session:
        result = await session.execute(
            select(InterferenceZone).where(InterferenceZone.id == zone_id)
        )
        zone = result.scalar_one_or_none()
        if not zone:
            raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found")

        result = await session.execute(
            select(AnomalyEvent)
            .where(AnomalyEvent.zone_event_id == zone_id)
            .order_by(AnomalyEvent.ts.desc())
            .limit(100)
        )
        events = result.scalars().all()

    event_responses = []
    for e in events:
        event_responses.append({
            "id": e.id,
            "ts": e.ts,
            "icao24": e.icao24,
            "callsign": e.callsign,
            "latitude": e.latitude,
            "longitude": e.longitude,
            "altitude_m": e.altitude_m,
            "anomaly_type": e.anomaly_type,
            "severity": e.severity,
            "severity_label": e.severity_label,
            "flags": e.flags if isinstance(e.flags, list) else [],
        })

    return {
        "zone": _zone_to_response(zone),
        "events": event_responses,
    }


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


@router.get("/api/stats", response_model=StatsResponse)
async def get_stats() -> dict:
    """
    Get global dashboard statistics.

    Computes aggregate counts across all events and zones, including
    live polling status from the in-memory cache.
    """
    from app.main import live_state

    async with async_session() as session:
        result = await session.execute(select(func.count(AnomalyEvent.id)))
        total_events = result.scalar() or 0

        result = await session.execute(select(func.count(InterferenceZone.id)))
        total_zones = result.scalar() or 0

        result = await session.execute(
            select(func.count(func.distinct(AnomalyEvent.icao24)))
        )
        total_aircraft = result.scalar() or 0

        result = await session.execute(
            select(func.min(AnomalyEvent.ts), func.max(AnomalyEvent.ts))
        )
        row = result.one()
        min_date = row[0] or datetime(2025, 10, 1, tzinfo=timezone.utc)
        max_date = row[1] or datetime(2026, 3, 30, tzinfo=timezone.utc)

        result = await session.execute(
            select(AnomalyEvent.anomaly_type, func.count(AnomalyEvent.id))
            .group_by(AnomalyEvent.anomaly_type)
        )
        by_type_dict = dict(result.all())

        result = await session.execute(select(func.avg(AnomalyEvent.severity)))
        avg_severity = result.scalar() or 0.0

        result = await session.execute(
            select(func.count(InterferenceZone.id)).where(
                InterferenceZone.status == "active"
            )
        )
        active_zones = result.scalar() or 0

        hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        result = await session.execute(
            select(func.count(AnomalyEvent.id)).where(AnomalyEvent.ts >= hour_ago)
        )
        events_last_hour = result.scalar() or 0

    return {
        "total_events": total_events,
        "total_zones": total_zones,
        "total_aircraft_affected": total_aircraft,
        "date_range": {
            "start": min_date.date() if hasattr(min_date, "date") else min_date,
            "end": max_date.date() if hasattr(max_date, "date") else max_date,
        },
        "by_type": {
            "spoofing": by_type_dict.get("spoofing", 0),
            "jamming": by_type_dict.get("jamming", 0),
            "mixed": by_type_dict.get("anomaly", 0),
        },
        "avg_severity": round(float(avg_severity), 1),
        "live": {
            "active_zones": active_zones,
            "events_last_hour": events_last_hour,
            "last_poll": live_state.get("last_poll"),
            "poll_status": live_state.get("poll_status", "inactive"),
        },
    }


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------


@router.get("/api/findings", response_model=FindingsResponse)
async def get_findings() -> dict:
    """
    Get pre-computed key findings for the narrative dashboard.
    """
    async with async_session() as session:
        result = await session.execute(
            select(Finding).order_by(Finding.sort_order)
        )
        findings = result.scalars().all()

    computed_at = findings[0].computed_at if findings else None

    return {
        "findings": [
            {
                "finding_key": f.finding_key,
                "title": f.title,
                "value": f.value,
                "detail": f.detail,
            }
            for f in findings
        ],
        "computed_at": computed_at,
    }


# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------

# Human-readable region names.
REGION_DISPLAY_NAMES = {
    "baltic_sea": "Baltic Sea / Eastern Europe",
    "eastern_med": "Eastern Mediterranean",
    "persian_gulf": "Persian Gulf",
    "red_sea": "Red Sea / Gulf of Aden",
    "black_sea": "Black Sea",
    "ukraine_frontline": "Ukraine Frontline",
    "south_china_sea": "South China Sea",
    "other": "Other / Unknown",
}


@router.get("/api/regions", response_model=RegionsResponse)
async def get_regions(
    period: Literal["daily", "weekly", "monthly"] = Query(default="monthly", description="daily, weekly, or monthly"),
) -> dict:
    """
    Get per-region breakdown with trend data.
    """
    async with async_session() as session:
        result = await session.execute(
            select(
                AnomalyEvent.region,
                func.count(AnomalyEvent.id).label("total"),
                func.count(AnomalyEvent.id).filter(
                    AnomalyEvent.anomaly_type == "spoofing"
                ).label("spoofing"),
                func.count(AnomalyEvent.id).filter(
                    AnomalyEvent.anomaly_type == "jamming"
                ).label("jamming"),
                func.count(func.distinct(AnomalyEvent.icao24)).label("aircraft"),
                func.avg(AnomalyEvent.severity).label("avg_sev"),
            ).group_by(AnomalyEvent.region)
            .order_by(text("total DESC"))
        )
        region_rows = result.all()

        result = await session.execute(
            select(RegionStat)
            .where(RegionStat.period == period)
            .order_by(RegionStat.region, RegionStat.period_start)
        )
        stats = result.scalars().all()

    trends: dict[str, list[dict]] = {}
    for stat in stats:
        trends.setdefault(stat.region, []).append({
            "period": stat.period_start.strftime(
                "%Y-%m-%d" if period == "daily"
                else "%Y-W%V" if period == "weekly"
                else "%Y-%m"
            ),
            "events": stat.total_events,
        })

    regions = []
    for row in region_rows:
        region_id = row[0]
        regions.append({
            "region": region_id,
            "name": REGION_DISPLAY_NAMES.get(region_id, region_id),
            "total_events": row[1],
            "spoofing_events": row[2],
            "jamming_events": row[3],
            "unique_aircraft": row[4],
            "avg_severity": round(float(row[5]), 1) if row[5] else 0.0,
            "trend": trends.get(region_id, []),
        })

    return {"regions": regions}
