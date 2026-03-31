"""
GPS Shield — Pydantic Response/Request Schemas.

All API request parameters and response shapes are defined here.
These must match the API contracts in Part 6 of the master plan exactly.
Frontend TypeScript types in lib/types.ts must mirror these schemas.

Used by:
    - api.py route handlers for response serialization.
    - tests for response shape validation.
    - Frontend developers as the source of truth for API contracts.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Zone schemas
# ---------------------------------------------------------------------------


class ZoneResponse(BaseModel):
    """
    A single interference zone as returned by the API.

    Contains geographic center, radius, classification, severity,
    and Pulsar mitigation data for the frontend toggle visualization.

    Attributes:
        id: Zone primary key.
        center_lat: Zone center latitude (WGS-84).
        center_lon: Zone center longitude (WGS-84).
        radius_km: Estimated GPS interference radius in km.
        event_type: 'spoofing', 'jamming', or 'mixed'.
        severity: 0-100 severity score.
        affected_aircraft: Number of aircraft affected.
        start_time: ISO 8601 UTC timestamp of zone start.
        end_time: ISO 8601 UTC timestamp of zone resolution, or null.
        status: 'active' or 'resolved'.
        region: Known region identifier.
        is_live: True if detected by live polling.
        gps_jam_radius_km: GPS jamming effective radius.
        pulsar_jam_radius_km: Reduced radius under Pulsar.
        spoofing_eliminated: True if Pulsar eliminates this spoofing.
        signal_advantage_db: Pulsar signal advantage in dB.
        area_reduction_pct: Area reduction percentage with Pulsar.
    """

    id: int
    center_lat: float
    center_lon: float
    radius_km: float
    event_type: str
    severity: int
    affected_aircraft: int
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str
    region: str
    is_live: bool
    gps_jam_radius_km: Optional[float] = None
    pulsar_jam_radius_km: Optional[float] = None
    spoofing_eliminated: bool
    signal_advantage_db: Optional[float] = None
    area_reduction_pct: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class ZonesLiveResponse(BaseModel):
    """
    Response for GET /api/zones/live — currently active zones.

    Attributes:
        count: Number of active zones returned.
        last_poll: ISO 8601 timestamp of last OpenSky poll.
        poll_status: 'active', 'delayed', or 'inactive'.
        zones: List of active interference zones.
    """

    count: int
    last_poll: Optional[datetime] = None
    poll_status: str
    zones: list[ZoneResponse]


class ZonesHistoryResponse(BaseModel):
    """
    Response for GET /api/zones/history — paginated historical zones.

    Attributes:
        total_count: Total matching zones across all pages.
        page: Current page number.
        page_size: Number of zones per page.
        zones: List of zones for the current page.
    """

    total_count: int
    page: int
    page_size: int
    zones: list[ZoneResponse]


# ---------------------------------------------------------------------------
# Event schemas
# ---------------------------------------------------------------------------


class AnomalyFlagResponse(BaseModel):
    """
    A single detector flag within an anomaly event.

    Attributes:
        detector: Name of the detector that fired.
        value: The measured value that triggered the flag.
        threshold: The threshold that was exceeded.
        confidence: Confidence score 0.0-1.0.
        detail: Human-readable description of the anomaly.
    """

    detector: str
    value: float
    threshold: float
    confidence: float
    detail: str


class EventResponse(BaseModel):
    """
    A single anomaly event (aircraft detection) as returned by the API.

    Attributes:
        id: Event primary key.
        ts: ISO 8601 UTC timestamp of detection.
        icao24: Aircraft hex identifier.
        callsign: Flight callsign.
        latitude: Detection latitude.
        longitude: Detection longitude.
        altitude_m: Detection altitude in meters.
        anomaly_type: 'spoofing', 'jamming', or 'anomaly'.
        severity: 0-100 severity score.
        severity_label: 'low', 'moderate', 'elevated', 'high', or 'critical'.
        flags: List of detector flags that triggered this event.
    """

    id: int
    ts: datetime
    icao24: str
    callsign: Optional[str] = None
    latitude: float
    longitude: float
    altitude_m: Optional[float] = None
    anomaly_type: str
    severity: int
    severity_label: str
    flags: list[AnomalyFlagResponse]

    model_config = ConfigDict(from_attributes=True)


class ZoneDetailResponse(BaseModel):
    """
    Response for GET /api/zones/{zone_id} — zone with all its events.

    Attributes:
        zone: Full zone object.
        events: List of anomaly events belonging to this zone.
    """

    zone: ZoneResponse
    events: list[EventResponse]


# ---------------------------------------------------------------------------
# Stats schemas
# ---------------------------------------------------------------------------


class DateRangeResponse(BaseModel):
    """
    Date range for analysis period.

    Attributes:
        start: Start date of analysis.
        end: End date of analysis.
    """

    start: date
    end: date


class ByTypeResponse(BaseModel):
    """
    Event counts broken down by type.

    Attributes:
        spoofing: Count of spoofing events.
        jamming: Count of jamming events.
        mixed: Count of mixed events.
    """

    spoofing: int
    jamming: int
    mixed: int


class LiveStatsResponse(BaseModel):
    """
    Live polling status information.

    Attributes:
        active_zones: Number of currently active zones.
        events_last_hour: Events detected in the last hour.
        last_poll: Timestamp of last OpenSky poll.
        poll_status: 'active', 'delayed', or 'inactive'.
    """

    active_zones: int
    events_last_hour: int
    last_poll: Optional[datetime] = None
    poll_status: str


class StatsResponse(BaseModel):
    """
    Response for GET /api/stats — global dashboard statistics.

    Attributes:
        total_events: Total anomaly events in database.
        total_zones: Total interference zones.
        total_aircraft_affected: Unique aircraft affected.
        date_range: Analysis period start/end dates.
        by_type: Event counts by type.
        avg_severity: Average severity across all events.
        live: Current live polling statistics.
    """

    total_events: int
    total_zones: int
    total_aircraft_affected: int
    date_range: DateRangeResponse
    by_type: ByTypeResponse
    avg_severity: float
    live: LiveStatsResponse


# ---------------------------------------------------------------------------
# Findings schemas
# ---------------------------------------------------------------------------


class FindingResponse(BaseModel):
    """
    A single pre-computed key finding.

    Attributes:
        finding_key: Unique identifier for the finding.
        title: Display title.
        value: Headline value (e.g., '12,847').
        detail: Extended description text.
    """

    finding_key: str
    title: str
    value: str
    detail: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class FindingsResponse(BaseModel):
    """
    Response for GET /api/findings — all pre-computed findings.

    Attributes:
        findings: List of key findings.
        computed_at: When findings were last computed.
    """

    findings: list[FindingResponse]
    computed_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Region schemas
# ---------------------------------------------------------------------------


class TrendPointResponse(BaseModel):
    """
    A single data point in a region's trend series.

    Attributes:
        period: Period label (e.g., '2025-10').
        events: Event count for this period.
    """

    period: str
    events: int


class RegionResponse(BaseModel):
    """
    Per-region breakdown with trend data.

    Attributes:
        region: Region identifier.
        name: Human-readable region name.
        total_events: Total events in this region.
        spoofing_events: Spoofing event count.
        jamming_events: Jamming event count.
        unique_aircraft: Unique aircraft affected.
        avg_severity: Average severity for this region.
        trend: Time series of event counts by period.
    """

    region: str
    name: str
    total_events: int
    spoofing_events: int
    jamming_events: int
    unique_aircraft: int
    avg_severity: float
    trend: list[TrendPointResponse]


class RegionsResponse(BaseModel):
    """
    Response for GET /api/regions — all region breakdowns.

    Attributes:
        regions: List of per-region data with trends.
    """

    regions: list[RegionResponse]


# ---------------------------------------------------------------------------
# Health schema
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    """
    Response for GET /health — system health status.

    Attributes:
        status: Overall status ('healthy' or 'degraded').
        database: Database connection status ('connected' or 'disconnected').
        live_polling: Polling status ('active', 'inactive', or 'error').
        last_poll: Timestamp of last successful poll.
        version: Application version string.
    """

    status: str
    database: str
    live_polling: str
    last_poll: Optional[datetime] = None
    version: str
