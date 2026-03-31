"""
001 — Initial database schema for GPS Shield.

Creates all four tables with indexes and constraints:
    - interference_zones: Clustered GPS interference zones with Pulsar data.
    - anomaly_events: Individual aircraft anomaly detections.
    - findings: Pre-computed key findings for narrative dashboard.
    - region_stats: Regional aggregate statistics.

Revision ID: 001_initial
Revises: None
Create Date: 2026-03-31
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# Revision identifiers
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all GPS Shield database tables, indexes, and constraints."""

    # -- interference_zones --
    op.create_table(
        "interference_zones",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("center_lat", sa.Double(), nullable=False),
        sa.Column("center_lon", sa.Double(), nullable=False),
        sa.Column("radius_km", sa.Double(), nullable=False),
        sa.Column("event_type", sa.String(10), nullable=False),
        sa.Column("severity", sa.SmallInteger(), nullable=False),
        sa.Column("affected_aircraft", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(10), nullable=False, server_default="'active'"),
        sa.Column("region", sa.String(30), nullable=False),
        sa.Column("is_live", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("gps_jam_radius_km", sa.Double(), nullable=True),
        sa.Column("pulsar_jam_radius_km", sa.Double(), nullable=True),
        sa.Column("spoofing_eliminated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("signal_advantage_db", sa.Double(), nullable=True),
        sa.Column("area_reduction_pct", sa.Double(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("event_type IN ('spoofing', 'jamming', 'mixed')", name="ck_zone_event_type"),
        sa.CheckConstraint("severity BETWEEN 0 AND 100", name="ck_zone_severity"),
        sa.CheckConstraint("status IN ('active', 'resolved')", name="ck_zone_status"),
    )
    op.create_index("idx_zones_status", "interference_zones", ["status"], postgresql_where=sa.text("status = 'active'"))
    op.create_index("idx_zones_region", "interference_zones", ["region", sa.text("start_time DESC")])
    op.create_index("idx_zones_time", "interference_zones", [sa.text("start_time DESC")])
    op.create_index("idx_zones_coords", "interference_zones", ["center_lat", "center_lon"])

    # -- anomaly_events --
    op.create_table(
        "anomaly_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("icao24", sa.String(6), nullable=False),
        sa.Column("callsign", sa.String(8), nullable=True),
        sa.Column("latitude", sa.Double(), nullable=False),
        sa.Column("longitude", sa.Double(), nullable=False),
        sa.Column("altitude_m", sa.Double(), nullable=True),
        sa.Column("anomaly_type", sa.String(10), nullable=False),
        sa.Column("severity", sa.SmallInteger(), nullable=False),
        sa.Column("severity_label", sa.String(10), nullable=False),
        sa.Column("flags", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("zone_event_id", sa.BigInteger(), sa.ForeignKey("interference_zones.id"), nullable=True),
        sa.Column("region", sa.String(30), nullable=False),
        sa.Column("is_live", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("anomaly_type IN ('spoofing', 'jamming', 'anomaly')", name="ck_event_anomaly_type"),
        sa.CheckConstraint("severity BETWEEN 0 AND 100", name="ck_event_severity"),
    )
    op.create_index("idx_events_ts", "anomaly_events", [sa.text("ts DESC")])
    op.create_index("idx_events_region_ts", "anomaly_events", ["region", sa.text("ts DESC")])
    op.create_index("idx_events_type", "anomaly_events", ["anomaly_type", sa.text("ts DESC")])
    op.create_index("idx_events_zone", "anomaly_events", ["zone_event_id"])
    op.create_index("idx_events_severity", "anomaly_events", [sa.text("severity DESC")], postgresql_where=sa.text("anomaly_type != 'anomaly'"))
    op.create_index("idx_events_coords", "anomaly_events", ["latitude", "longitude"])

    # -- findings --
    op.create_table(
        "findings",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("finding_key", sa.String(50), unique=True, nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    # -- region_stats --
    op.create_table(
        "region_stats",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("region", sa.String(30), nullable=False),
        sa.Column("period", sa.String(10), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("total_events", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("spoofing_events", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("jamming_events", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unique_aircraft", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_severity", sa.Double(), nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("region", "period", "period_start", name="uq_region_stats"),
    )
    op.create_index("idx_region_stats_lookup", "region_stats", ["region", "period", sa.text("period_start DESC")])


def downgrade() -> None:
    """Drop all GPS Shield database tables."""
    op.drop_table("anomaly_events")
    op.drop_table("interference_zones")
    op.drop_table("region_stats")
    op.drop_table("findings")
