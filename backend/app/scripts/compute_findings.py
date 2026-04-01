"""
GPS Shield — Key Findings Computation Script.

Queries the database after historical data is loaded and computes
the 5 key findings from Part 4.3 of the master plan. Also computes
regional aggregate statistics for the dashboard.

Usage:
    python -m app.scripts.compute_findings

Computes:
    1. Total events detected across all zones.
    2. Most affected region (Baltic Sea dominance).
    3. Quarter-over-quarter trend.
    4. Total aircraft affected.
    5. Pulsar impact summary (spoofing elimination + area reduction).
"""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import func, select, text

from app.database import async_session, engine
from app.models import AnomalyEvent, Base, Finding, RegionStat
from app.detection import REGION_NAMES

logger = logging.getLogger(__name__)


async def compute_findings() -> None:
    """
    Compute all 5 key findings and store them in the findings table.

    Queries anomaly_events and interference_zones to derive headline
    statistics for the Key Findings page.
    """
    async with async_session() as session:
        # Total events.
        result = await session.execute(
            select(func.count(AnomalyEvent.id))
        )
        total_events = result.scalar() or 0

        # Date range.
        result = await session.execute(
            select(func.min(AnomalyEvent.ts), func.max(AnomalyEvent.ts))
        )
        row = result.one()
        min_date = row[0]
        max_date = row[1]
        date_range_str = ""
        if min_date and max_date:
            date_range_str = f"{min_date.strftime('%B %Y')} — {max_date.strftime('%B %Y')}"

        # By type.
        result = await session.execute(
            select(
                AnomalyEvent.anomaly_type,
                func.count(AnomalyEvent.id),
            ).group_by(AnomalyEvent.anomaly_type)
        )
        by_type = dict(result.all())
        spoofing_count = by_type.get("spoofing", 0)
        jamming_count = by_type.get("jamming", 0)

        # Most affected region.
        result = await session.execute(
            select(
                AnomalyEvent.region,
                func.count(AnomalyEvent.id).label("cnt"),
            ).group_by(AnomalyEvent.region).order_by(text("cnt DESC")).limit(1)
        )
        top_region_row = result.first()
        top_region = top_region_row[0] if top_region_row else "unknown"
        top_region_count = top_region_row[1] if top_region_row else 0
        top_region_pct = round(top_region_count / max(total_events, 1) * 100)
        top_region_name = REGION_NAMES.get(top_region, top_region)

        # Daily average for top region.
        if min_date and max_date:
            total_days = max((max_date - min_date).days, 1)
            daily_avg = round(top_region_count / total_days)
        else:
            daily_avg = 0

        # Unique aircraft affected.
        result = await session.execute(
            select(func.count(func.distinct(AnomalyEvent.icao24)))
        )
        unique_aircraft = result.scalar() or 0

        # Aircraft with large position errors (severity > 60).
        result = await session.execute(
            select(func.count(func.distinct(AnomalyEvent.icao24))).where(
                AnomalyEvent.severity > 60
            )
        )
        severe_aircraft = result.scalar() or 0

        # Quarter-over-quarter trend.
        # Q4 2025: Oct-Dec. Q1 2026: Jan-Mar.
        result = await session.execute(
            select(func.count(AnomalyEvent.id)).where(
                AnomalyEvent.ts >= datetime(2025, 10, 1, tzinfo=timezone.utc),
                AnomalyEvent.ts < datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
        )
        q4_count = result.scalar() or 0

        result = await session.execute(
            select(func.count(AnomalyEvent.id)).where(
                AnomalyEvent.ts >= datetime(2026, 1, 1, tzinfo=timezone.utc),
                AnomalyEvent.ts < datetime(2026, 4, 1, tzinfo=timezone.utc),
            )
        )
        q1_count = result.scalar() or 0

        if q4_count > 0:
            qoq_change = round((q1_count - q4_count) / q4_count * 100)
        else:
            qoq_change = 0

        # Upsert findings.
        findings_data = [
            {
                "finding_key": "total_events",
                "title": "GPS Interference Events Detected",
                "value": f"{total_events:,}",
                "detail": f"Across 7 known conflict zones, {date_range_str}",
                "sort_order": 1,
            },
            {
                "finding_key": "baltic_dominance",
                "title": f"{top_region_name}: Epicenter of GPS Spoofing",
                "value": f"{top_region_pct}%",
                "detail": (
                    f"The {top_region_name} region accounts for {top_region_pct}% "
                    f"of all detected spoofing events, averaging {daily_avg} incidents per day"
                ),
                "sort_order": 2,
            },
            {
                "finding_key": "trend",
                "title": "Quarter-over-Quarter Increase",
                "value": f"+{qoq_change}%" if qoq_change > 0 else f"{qoq_change}%",
                "detail": f"GPS interference: {q1_count:,} events in Q1 2026 vs {q4_count:,} in Q4 2025",
                "sort_order": 3,
            },
            {
                "finding_key": "aircraft_affected",
                "title": "Unique Aircraft Affected",
                "value": f"{unique_aircraft:,}",
                "detail": (
                    f"Including {severe_aircraft:,} flights with high-severity "
                    f"anomalies (severity > 60)"
                ),
                "sort_order": 4,
            },
            {
                "finding_key": "pulsar_impact",
                "title": "What Pulsar Would Change",
                "value": "100% spoofing eliminated",
                "detail": (
                    f"Pulsar's cryptographic authentication would eliminate all "
                    f"{spoofing_count:,} spoofing events. Its 100x signal strength "
                    f"would reduce the effective area of all {jamming_count:,} "
                    f"jamming events by 97%."
                ),
                "sort_order": 5,
            },
        ]

        for fd in findings_data:
            existing = await session.execute(
                select(Finding).where(Finding.finding_key == fd["finding_key"])
            )
            finding = existing.scalar_one_or_none()
            if finding:
                finding.title = fd["title"]
                finding.value = fd["value"]
                finding.detail = fd["detail"]
                finding.sort_order = fd["sort_order"]
                finding.computed_at = datetime.now(timezone.utc)
            else:
                session.add(Finding(**fd, computed_at=datetime.now(timezone.utc)))

        await session.commit()

    print("Key findings computed and stored:")
    for fd in findings_data:
        print(f"  {fd['finding_key']}: {fd['value']}")


async def compute_region_stats() -> None:
    """
    Compute monthly regional aggregate statistics.

    Populates the region_stats table with per-region, per-month rollups
    of anomaly event data for the dashboard trend charts.
    """
    async with async_session() as session:
        # Get distinct region + month combos.
        result = await session.execute(text("""
            SELECT
                region,
                DATE_TRUNC('month', ts) AS month_start,
                COUNT(*) AS total_events,
                COUNT(*) FILTER (WHERE anomaly_type = 'spoofing') AS spoofing_events,
                COUNT(*) FILTER (WHERE anomaly_type = 'jamming') AS jamming_events,
                COUNT(DISTINCT icao24) AS unique_aircraft,
                AVG(severity) AS avg_severity
            FROM anomaly_events
            GROUP BY region, DATE_TRUNC('month', ts)
            ORDER BY region, month_start
        """))

        rows = result.all()

        for row in rows:
            existing = await session.execute(
                select(RegionStat).where(
                    RegionStat.region == row[0],
                    RegionStat.period == "monthly",
                    RegionStat.period_start == row[1].date(),
                )
            )
            stat = existing.scalar_one_or_none()
            if stat:
                stat.total_events = row[2]
                stat.spoofing_events = row[3]
                stat.jamming_events = row[4]
                stat.unique_aircraft = row[5]
                stat.avg_severity = float(row[6]) if row[6] else None
                stat.computed_at = datetime.now(timezone.utc)
            else:
                session.add(RegionStat(
                    region=row[0],
                    period="monthly",
                    period_start=row[1].date(),
                    total_events=row[2],
                    spoofing_events=row[3],
                    jamming_events=row[4],
                    unique_aircraft=row[5],
                    avg_severity=float(row[6]) if row[6] else None,
                    computed_at=datetime.now(timezone.utc),
                ))

        await session.commit()

    print(f"Region stats computed: {len(rows)} monthly aggregates")


async def main() -> None:
    """CLI entry point — compute all findings and region stats."""
    print("GPS Shield — Computing Key Findings")
    print("=" * 50)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await compute_findings()
    await compute_region_stats()

    await engine.dispose()
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
