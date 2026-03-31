"""
GPS Shield — SQLAlchemy ORM Models.

Defines all database tables for the GPS Shield platform:
    - AnomalyEvent: Individual aircraft anomaly detections.
    - InterferenceZone: Clustered interference zones with Pulsar mitigation data.
    - Finding: Pre-computed key findings for the narrative dashboard.
    - RegionStat: Regional aggregate statistics for trend analysis.

All models match the schema defined in Part 5 of the master plan exactly,
including constraints, indexes, and default values.
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Double,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class InterferenceZone(Base):
    """
    A geographic interference zone formed by clustering anomaly events.

    Represents a detected area of GPS spoofing, jamming, or mixed interference.
    Includes Pulsar mitigation data used by the frontend toggle visualization.

    Attributes:
        id: Auto-incrementing primary key.
        center_lat: Zone center latitude (WGS-84 degrees).
        center_lon: Zone center longitude (WGS-84 degrees).
        radius_km: Estimated GPS interference radius in kilometers.
        event_type: Type of interference ('spoofing', 'jamming', 'mixed').
        severity: Severity score 0-100.
        affected_aircraft: Count of aircraft affected by this zone.
        start_time: When the zone was first detected.
        end_time: When the zone was resolved (null if still active).
        status: Zone status ('active' or 'resolved').
        region: Known interference region identifier.
        is_live: Whether this zone was detected by live polling.
        gps_jam_radius_km: Estimated GPS jamming radius.
        pulsar_jam_radius_km: Reduced radius under Pulsar protection.
        spoofing_eliminated: Whether Pulsar would eliminate this spoofing.
        signal_advantage_db: Pulsar signal advantage in dB.
        area_reduction_pct: Percentage of area reduction with Pulsar.
        created_at: Row creation timestamp.
    """

    __tablename__ = "interference_zones"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    center_lat: Mapped[float] = mapped_column(Double, nullable=False)
    center_lon: Mapped[float] = mapped_column(Double, nullable=False)
    radius_km: Mapped[float] = mapped_column(Double, nullable=False)
    event_type: Mapped[str] = mapped_column(String(10), nullable=False)
    severity: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    affected_aircraft: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="active")
    region: Mapped[str] = mapped_column(String(30), nullable=False)
    is_live: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Pulsar mitigation data
    gps_jam_radius_km: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    pulsar_jam_radius_km: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    spoofing_eliminated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    signal_advantage_db: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    area_reduction_pct: Mapped[Optional[float]] = mapped_column(Double, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="NOW()"
    )

    # Relationships
    events: Mapped[list["AnomalyEvent"]] = relationship(back_populates="zone")

    __table_args__ = (
        CheckConstraint("event_type IN ('spoofing', 'jamming', 'mixed')", name="ck_zone_event_type"),
        CheckConstraint("severity BETWEEN 0 AND 100", name="ck_zone_severity"),
        CheckConstraint("status IN ('active', 'resolved')", name="ck_zone_status"),
        Index("idx_zones_status", "status", postgresql_where="status = 'active'"),
        Index("idx_zones_region", "region", start_time.desc()),
        Index("idx_zones_time", start_time.desc()),
        Index("idx_zones_coords", "center_lat", "center_lon"),
    )


class AnomalyEvent(Base):
    """
    An individual aircraft anomaly detection.

    Each row represents a single aircraft at a single point in time that
    exhibited anomalous GPS behavior (spoofing, jamming, or unclassified).

    Attributes:
        id: Auto-incrementing primary key.
        ts: Timestamp of the anomaly detection.
        icao24: Aircraft hex identifier (6 chars).
        callsign: Flight callsign (up to 8 chars).
        latitude: Aircraft latitude at detection time.
        longitude: Aircraft longitude at detection time.
        altitude_m: Aircraft altitude in meters.
        anomaly_type: Classification ('spoofing', 'jamming', 'anomaly').
        severity: Severity score 0-100.
        severity_label: Human-readable severity ('low' through 'critical').
        flags: JSONB array of detector flags with confidence scores.
        zone_event_id: FK to the parent interference zone.
        region: Known interference region identifier.
        is_live: Whether detected by live polling.
        created_at: Row creation timestamp.
    """

    __tablename__ = "anomaly_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    icao24: Mapped[str] = mapped_column(String(6), nullable=False)
    callsign: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    latitude: Mapped[float] = mapped_column(Double, nullable=False)
    longitude: Mapped[float] = mapped_column(Double, nullable=False)
    altitude_m: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    anomaly_type: Mapped[str] = mapped_column(String(10), nullable=False)
    severity: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    severity_label: Mapped[str] = mapped_column(String(10), nullable=False)
    flags: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="'[]'::jsonb")
    zone_event_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("interference_zones.id"), nullable=True
    )
    region: Mapped[str] = mapped_column(String(30), nullable=False)
    is_live: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="NOW()"
    )

    # Relationships
    zone: Mapped[Optional["InterferenceZone"]] = relationship(back_populates="events")

    __table_args__ = (
        CheckConstraint(
            "anomaly_type IN ('spoofing', 'jamming', 'anomaly')", name="ck_event_anomaly_type"
        ),
        CheckConstraint("severity BETWEEN 0 AND 100", name="ck_event_severity"),
        Index("idx_events_ts", ts.desc()),
        Index("idx_events_region_ts", "region", ts.desc()),
        Index("idx_events_type", "anomaly_type", ts.desc()),
        Index("idx_events_zone", "zone_event_id"),
        Index(
            "idx_events_severity",
            severity.desc(),
            postgresql_where="anomaly_type != 'anomaly'",
        ),
        Index("idx_events_coords", "latitude", "longitude"),
    )


class Finding(Base):
    """
    A pre-computed key finding for the narrative dashboard.

    Findings are computed by compute_findings.py after historical data
    is loaded. They provide the headline statistics displayed on the
    Key Findings page.

    Attributes:
        id: Auto-incrementing primary key.
        finding_key: Unique identifier for the finding (e.g., 'total_events').
        title: Display title.
        value: The headline value (e.g., '12,847').
        detail: Extended description text.
        sort_order: Display ordering.
        computed_at: When this finding was last computed.
    """

    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    finding_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="NOW()"
    )


class RegionStat(Base):
    """
    Regional aggregate statistics for dashboard trend analysis.

    Pre-computed per-region, per-period rollups of anomaly event data.
    Used by GET /api/regions for the region breakdown sidebar and charts.

    Attributes:
        id: Auto-incrementing primary key.
        region: Region identifier.
        period: Aggregation period ('daily', 'weekly', 'monthly').
        period_start: Start date of the aggregation period.
        total_events: Total anomaly events in this period.
        spoofing_events: Count of spoofing events.
        jamming_events: Count of jamming events.
        unique_aircraft: Count of unique aircraft affected.
        avg_severity: Average severity score.
        computed_at: When these stats were last computed.
    """

    __tablename__ = "region_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    region: Mapped[str] = mapped_column(String(30), nullable=False)
    period: Mapped[str] = mapped_column(String(10), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    total_events: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    spoofing_events: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    jamming_events: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unique_aircraft: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_severity: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="NOW()"
    )

    __table_args__ = (
        UniqueConstraint("region", "period", "period_start", name="uq_region_stats"),
        Index("idx_region_stats_lookup", "region", "period", period_start.desc()),
    )
