"""
GPS Shield — Historical Data Batch Loader.

Queries the OpenSky Network historical API for state vectors at hourly
intervals over a given date range. Each snapshot is processed through
the anomaly detection pipeline and results are stored in PostgreSQL.

Usage:
    python -m app.scripts.load_historical --start 2025-10-01 --end 2026-03-30

Features:
    - Checkpoint/resume: tracks progress in a JSON file, resumes on restart.
    - Rate limit aware: respects 5-second minimum request intervals.
    - Progress bar (tqdm) with ETA.
    - Processes snapshots through the full detection pipeline.
    - Stores anomaly events and interference zones to the database.
"""

import argparse
import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tqdm import tqdm

from app.database import async_session, engine
from app.detection import AnomalyPipeline, ClassifiedAnomaly, ZoneData
from app.ingestion import OpenSkyClient
from app.models import AnomalyEvent, Base, InterferenceZone

logger = logging.getLogger(__name__)

CHECKPOINT_FILE = Path("historical_checkpoint.json")


def _parse_args() -> argparse.Namespace:
    """
    Parse CLI arguments for the historical loader.

    Returns:
        Namespace with start, end, and interval_hours attributes.
    """
    parser = argparse.ArgumentParser(description="Load historical OpenSky data")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--interval-hours", type=int, default=1, help="Hours between snapshots")
    return parser.parse_args()


def _load_checkpoint() -> int:
    """
    Load the last processed timestamp from checkpoint file.

    Returns:
        Unix timestamp of the last completed snapshot, or 0 if none.
    """
    if CHECKPOINT_FILE.exists():
        data = json.loads(CHECKPOINT_FILE.read_text())
        return data.get("last_timestamp", 0)
    return 0


def _save_checkpoint(timestamp: int) -> None:
    """
    Save progress to checkpoint file.

    Args:
        timestamp: Unix timestamp of the last completed snapshot.
    """
    CHECKPOINT_FILE.write_text(json.dumps({"last_timestamp": timestamp}))


async def load_historical(start_date: str, end_date: str, interval_hours: int = 1) -> None:
    """
    Load and process historical OpenSky data over a date range.

    Iterates hour by hour from start_date to end_date, fetching state
    vectors from OpenSky and running them through the anomaly pipeline.
    Results are stored in the database.

    Args:
        start_date: Start date string (YYYY-MM-DD).
        end_date: End date string (YYYY-MM-DD).
        interval_hours: Hours between snapshots (default 1).
    """
    start = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    # Create tables if needed.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Calculate timestamps.
    timestamps: list[int] = []
    current = start
    while current <= end:
        timestamps.append(int(current.timestamp()))
        current += timedelta(hours=interval_hours)

    # Resume from checkpoint.
    last_processed = _load_checkpoint()
    remaining = [ts for ts in timestamps if ts > last_processed]

    if last_processed > 0:
        print(f"Resuming from checkpoint: {datetime.fromtimestamp(last_processed, tz=timezone.utc)}")
        print(f"Remaining: {len(remaining)}/{len(timestamps)} snapshots")

    client = OpenSkyClient()
    pipeline = AnomalyPipeline()
    total_events = 0
    total_zones = 0

    try:
        with tqdm(remaining, desc="Loading historical data", unit="snapshot") as pbar:
            for ts in pbar:
                dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                pbar.set_postfix_str(f"{dt:%Y-%m-%d %H:%M}")

                # Fetch snapshot.
                raw_states = await client.fetch_states(timestamp=ts)
                if not raw_states:
                    _save_checkpoint(ts)
                    continue

                # Process through pipeline.
                events, zones = pipeline.process_snapshot(raw_states, snapshot_time=ts)

                # Store results if any anomalies found.
                if events or zones:
                    await _store_results(events, zones, ts)
                    total_events += len(events)
                    total_zones += len(zones)

                _save_checkpoint(ts)

    finally:
        await client.close()
        await engine.dispose()

    print("\nHistorical loading complete!")
    print(f"  Snapshots processed: {len(remaining)}")
    print(f"  Anomaly events: {total_events:,}")
    print(f"  Interference zones: {total_zones:,}")


async def _store_results(
    events: list[ClassifiedAnomaly],
    zones: list[ZoneData],
    snapshot_time: int,
) -> None:
    """
    Store detection pipeline results in the database.

    Args:
        events: List of ClassifiedAnomaly from the pipeline.
        zones: List of ZoneData from the pipeline.
        snapshot_time: Unix timestamp of the snapshot.
    """
    async with async_session() as session:
        # Insert zones first.
        db_zones = []
        for zone in zones:
            iz = InterferenceZone(
                center_lat=zone.center_lat,
                center_lon=zone.center_lon,
                radius_km=zone.radius_km,
                event_type=zone.event_type,
                severity=zone.severity,
                affected_aircraft=zone.affected_aircraft,
                start_time=zone.start_time,
                end_time=zone.end_time,
                status="resolved",
                region=zone.region,
                is_live=False,
                gps_jam_radius_km=zone.gps_jam_radius_km,
                pulsar_jam_radius_km=zone.pulsar_jam_radius_km,
                spoofing_eliminated=zone.spoofing_eliminated,
                signal_advantage_db=zone.signal_advantage_db,
                area_reduction_pct=zone.area_reduction_pct,
            )
            session.add(iz)
            db_zones.append(iz)

        await session.flush()

        # Build a mapping from anomaly -> zone for correct assignment.
        anomaly_zone_map: dict[str, int] = {}
        for zi, zone in enumerate(zones):
            for a in zone.anomalies:
                key = f"{a.detection.aircraft.icao24}_{a.detection.aircraft.timestamp}"
                anomaly_zone_map[key] = zi

        # Insert events.
        for event in events:
            ac = event.detection.aircraft
            flags = [f.model_dump() for f in event.detection.flags]

            key = f"{ac.icao24}_{ac.timestamp}"
            zi = anomaly_zone_map.get(key)
            zone_id = (
                db_zones[zi].id if zi is not None and zi < len(db_zones)
                else (db_zones[0].id if db_zones else None)
            )

            ae = AnomalyEvent(
                ts=datetime.fromtimestamp(ac.timestamp, tz=timezone.utc),
                icao24=ac.icao24,
                callsign=ac.callsign or None,
                latitude=ac.latitude,
                longitude=ac.longitude,
                altitude_m=ac.geo_altitude if ac.geo_altitude is not None else ac.baro_altitude,
                anomaly_type=event.anomaly_type,
                severity=event.severity,
                severity_label=event.severity_label,
                flags=flags,
                zone_event_id=zone_id,
                region=event.region,
                is_live=False,
            )
            session.add(ae)

        await session.commit()


async def main() -> None:
    """CLI entry point."""
    args = _parse_args()
    await load_historical(args.start, args.end, args.interval_hours)


if __name__ == "__main__":
    asyncio.run(main())
