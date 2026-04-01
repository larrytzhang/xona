"""
002 — Add icao24 index to anomaly_events.

Adds a B-tree index on the icao24 column for faster per-aircraft lookups.

Revision ID: 002_add_icao24_index
Revises: 001_initial
Create Date: 2026-03-31
"""

from alembic import op

# Revision identifiers
revision = "002_add_icao24_index"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add icao24 index to anomaly_events."""
    op.create_index("idx_events_icao24", "anomaly_events", ["icao24"])


def downgrade() -> None:
    """Remove icao24 index."""
    op.drop_index("idx_events_icao24", table_name="anomaly_events")
