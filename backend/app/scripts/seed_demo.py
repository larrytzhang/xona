"""
GPS Shield — Demo Seed Data Generator.

Generates realistic synthetic anomaly data for all 7 known interference
zones, populating the database with 6 months of data. This ensures
the app ALWAYS looks impressive, even if OpenSky historical access
is unavailable.

Usage:
    python -m app.scripts.seed_demo

The generated data includes:
    - Anomaly events with realistic geographic distribution.
    - Interference zones with proper clustering.
    - Spoofing events concentrated in Baltic and Eastern Med.
    - Jamming events in conflict zones (Ukraine, Red Sea).
    - Realistic temporal patterns (increasing trend over 6 months).
    - Pulsar mitigation data on all zones.
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta, timezone


from app.database import async_session, engine
from app.models import AnomalyEvent, Base, InterferenceZone
from app.detection import KNOWN_ZONES, REGION_NAMES
from app.pulsar.interfaces.specs import (
    AREA_REDUCTION_PCT,
    RADIUS_REDUCTION_FACTOR,
    SIGNAL_ADVANTAGE_L1_DB,
)

logger = logging.getLogger(__name__)

# Date range for seed data.
SEED_START = datetime(2025, 10, 1, tzinfo=timezone.utc)
SEED_END = datetime(2026, 3, 30, tzinfo=timezone.utc)

# Per-zone event generation parameters.
ZONE_CONFIGS = {
    "baltic_sea": {"daily_events": (30, 60), "spoofing_pct": 0.86, "severity_range": (35, 85)},
    "eastern_med": {"daily_events": (20, 45), "spoofing_pct": 0.75, "severity_range": (30, 80)},
    "persian_gulf": {"daily_events": (15, 35), "spoofing_pct": 0.50, "severity_range": (25, 75)},
    "red_sea": {"daily_events": (10, 30), "spoofing_pct": 0.30, "severity_range": (30, 70)},
    "black_sea": {"daily_events": (15, 35), "spoofing_pct": 0.60, "severity_range": (25, 75)},
    "ukraine_frontline": {"daily_events": (20, 50), "spoofing_pct": 0.40, "severity_range": (40, 90)},
    "south_china_sea": {"daily_events": (8, 20), "spoofing_pct": 0.70, "severity_range": (20, 65)},
}

# Severity label mapping.
SEVERITY_LABELS = {
    (0, 20): "low",
    (20, 40): "moderate",
    (40, 60): "elevated",
    (60, 80): "high",
    (80, 101): "critical",
}


def _severity_label(severity: int) -> str:
    """
    Map a severity score to a label.

    Args:
        severity: Integer 0-100.

    Returns:
        Label string.
    """
    for (lo, hi), label in SEVERITY_LABELS.items():
        if lo <= severity < hi:
            return label
    return "critical"


def _random_callsign() -> str:
    """
    Generate a random realistic airline callsign.

    Returns:
        8-character callsign string like 'SWR1234 '.
    """
    prefixes = ["SWR", "DLH", "BAW", "AFR", "KLM", "UAE", "SIA", "QTR", "THY", "ACA",
                "ELY", "SVA", "ETD", "GIA", "MAS", "CPA", "AAL", "DAL", "UAL", "RYR"]
    return f"{random.choice(prefixes)}{random.randint(100, 9999):4d}"


def _random_icao24() -> str:
    """
    Generate a random hex aircraft identifier.

    Returns:
        6-character lowercase hex string.
    """
    return f"{random.randint(0, 0xFFFFFF):06x}"


def _trend_multiplier(day_offset: int, total_days: int) -> float:
    """
    Compute a trend multiplier that increases over time.

    Models the real-world increase in GPS interference incidents,
    with a sharper spike in the last quarter.

    Args:
        day_offset: Days since start of seed period.
        total_days: Total days in the seed period.

    Returns:
        Multiplier >= 0.5, increasing over time.
    """
    progress = day_offset / total_days
    # Starts at 0.5, ramps to 1.5 with a steeper curve at the end.
    return 0.5 + progress * 1.0 + (progress ** 3) * 0.5


async def generate_seed_data() -> dict:
    """
    Generate and insert all seed data into the database.

    Creates interference zones, anomaly events, findings, and region
    stats for a 6-month period across all 7 known zones.

    Returns:
        Dict with counts: total_events, total_zones, by_region.
    """
    total_days = (SEED_END - SEED_START).days
    all_zones: list[InterferenceZone] = []
    all_events: list[AnomalyEvent] = []
    stats_by_region: dict[str, dict] = {}

    for zone_info in KNOWN_ZONES:
        zone_id = zone_info.zone_id
        config = ZONE_CONFIGS[zone_id]
        region_events = 0
        region_spoofing = 0
        region_jamming = 0
        region_aircraft: set[str] = set()

        for day_offset in range(total_days):
            current_date = SEED_START + timedelta(days=day_offset)
            multiplier = _trend_multiplier(day_offset, total_days)

            # Generate daily events for this zone.
            min_events, max_events = config["daily_events"]
            daily_count = int(random.randint(min_events, max_events) * multiplier)

            # Create 1-3 zone clusters per day.
            num_clusters = random.randint(1, 3)
            for cluster_idx in range(num_clusters):
                cluster_size = max(3, daily_count // num_clusters)
                hour = random.randint(0, 23)
                minute = random.randint(0, 59)
                start_time = current_date.replace(hour=hour, minute=minute)

                # Zone center jittered from known center.
                jitter_lat = random.uniform(-2.0, 2.0)
                jitter_lon = random.uniform(-2.0, 2.0)
                center_lat = zone_info.center_lat + jitter_lat
                center_lon = zone_info.center_lon + jitter_lon

                severity = random.randint(*config["severity_range"])
                is_spoofing = random.random() < config["spoofing_pct"]
                event_type = "spoofing" if is_spoofing else "jamming"
                radius_km = random.uniform(50, min(zone_info.radius_km * 0.4, 300))

                # Create the interference zone.
                iz = InterferenceZone(
                    center_lat=center_lat,
                    center_lon=center_lon,
                    radius_km=radius_km,
                    event_type=event_type,
                    severity=severity,
                    affected_aircraft=cluster_size,
                    start_time=start_time,
                    end_time=start_time + timedelta(minutes=random.randint(10, 180)),
                    status="resolved",
                    region=zone_id,
                    is_live=False,
                    gps_jam_radius_km=radius_km,
                    pulsar_jam_radius_km=radius_km / RADIUS_REDUCTION_FACTOR,
                    spoofing_eliminated=is_spoofing,
                    signal_advantage_db=SIGNAL_ADVANTAGE_L1_DB,
                    area_reduction_pct=AREA_REDUCTION_PCT,
                )
                all_zones.append(iz)

                # Create events for this cluster.
                for _ in range(cluster_size):
                    icao = _random_icao24()
                    region_aircraft.add(icao)
                    evt_severity = max(0, min(100, severity + random.randint(-15, 15)))
                    evt_type = event_type if random.random() < 0.9 else "anomaly"

                    if evt_type == "spoofing":
                        region_spoofing += 1
                    elif evt_type == "jamming":
                        region_jamming += 1

                    flags = _generate_flags(evt_type)

                    evt = AnomalyEvent(
                        ts=start_time + timedelta(seconds=random.randint(0, 300)),
                        icao24=icao,
                        callsign=_random_callsign(),
                        latitude=center_lat + random.uniform(-0.5, 0.5),
                        longitude=center_lon + random.uniform(-0.5, 0.5),
                        altitude_m=random.uniform(3000, 12000),
                        anomaly_type=evt_type,
                        severity=evt_severity,
                        severity_label=_severity_label(evt_severity),
                        flags=flags,
                        region=zone_id,
                        is_live=False,
                    )
                    all_events.append(evt)
                    region_events += 1

        stats_by_region[zone_id] = {
            "total": region_events,
            "spoofing": region_spoofing,
            "jamming": region_jamming,
            "aircraft": len(region_aircraft),
        }

    # Batch insert into database.
    async with async_session() as session:
        # Insert zones first (events reference them).
        session.add_all(all_zones)
        await session.flush()

        # Link events to their zones.
        zone_idx = 0
        for i, evt in enumerate(all_events):
            # Simple assignment: events belong to the zone they were generated with.
            zone_for_event = all_zones[min(zone_idx, len(all_zones) - 1)]
            evt.zone_event_id = zone_for_event.id
            # Advance zone index roughly proportionally.
            if i > 0 and i % max(1, len(all_events) // len(all_zones)) == 0:
                zone_idx = min(zone_idx + 1, len(all_zones) - 1)

        session.add_all(all_events)
        await session.commit()

    total_events = len(all_events)
    total_zones = len(all_zones)

    print("\nSeed data generated:")
    print(f"  Total events:  {total_events:,}")
    print(f"  Total zones:   {total_zones:,}")
    print(f"  Date range:    {SEED_START.date()} to {SEED_END.date()}")
    print("\n  Per region:")
    for region, stats in stats_by_region.items():
        name = REGION_NAMES.get(region, region)
        print(f"    {name}: {stats['total']:,} events "
              f"({stats['spoofing']:,} spoofing, {stats['jamming']:,} jamming, "
              f"{stats['aircraft']:,} aircraft)")

    return {
        "total_events": total_events,
        "total_zones": total_zones,
        "by_region": stats_by_region,
    }


def _generate_flags(anomaly_type: str) -> list[dict]:
    """
    Generate realistic detector flag data for an anomaly event.

    Args:
        anomaly_type: 'spoofing', 'jamming', or 'anomaly'.

    Returns:
        List of flag dicts matching AnomalyFlag schema.
    """
    flags = []

    if anomaly_type == "spoofing":
        flags.append({
            "detector": "position_jump",
            "value": random.uniform(20000, 80000),
            "threshold": 12000,
            "confidence": random.uniform(0.6, 0.98),
            "detail": f"{random.uniform(20, 80):.1f} km jump in {random.randint(5, 15)} seconds",
        })
        if random.random() > 0.3:
            flags.append({
                "detector": "altitude",
                "value": random.uniform(200, 800),
                "threshold": 200,
                "confidence": random.uniform(0.4, 0.9),
                "detail": f"Baro-geo altitude divergence {random.uniform(200, 800):.0f} m",
            })
        if random.random() > 0.5:
            flags.append({
                "detector": "heading",
                "value": random.uniform(30, 150),
                "threshold": 30,
                "confidence": random.uniform(0.3, 0.85),
                "detail": f"Heading mismatch {random.uniform(30, 150):.1f}°",
            })
    elif anomaly_type == "jamming":
        flags.append({
            "detector": "velocity",
            "value": 0,
            "threshold": 0,
            "confidence": random.uniform(0.5, 0.9),
            "detail": "Signal loss detected — aircraft stopped reporting",
        })
    else:
        flags.append({
            "detector": "velocity",
            "value": random.uniform(340, 500),
            "threshold": 340,
            "confidence": random.uniform(0.2, 0.5),
            "detail": f"Reported velocity {random.uniform(340, 500):.1f} m/s",
        })

    return flags


async def create_tables() -> None:
    """
    Create all database tables if they don't exist.

    Uses SQLAlchemy metadata to create tables directly. In production,
    use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    """
    Main entry point for the seed data generator.

    Creates tables (if needed) and generates seed data.
    """
    print("GPS Shield — Demo Seed Data Generator")
    print("=" * 50)

    print("\nCreating database tables...")
    await create_tables()

    print("Generating seed data (this takes a few seconds)...")
    result = await generate_seed_data()

    print(f"\nDone! {result['total_events']:,} events across {result['total_zones']:,} zones.")
    print("Run compute_findings.py next to compute key findings.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
