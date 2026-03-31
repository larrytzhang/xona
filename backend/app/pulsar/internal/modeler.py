"""
Pulsar mitigation modeler.

Computes per-zone Pulsar impact metrics that drive the frontend's
Pulsar Mode toggle visualization. For each interference zone, calculates:
    - Reduced jamming radius under Pulsar protection.
    - Whether spoofing is eliminated (binary — crypto auth).
    - Signal advantage in dB.
    - Area reduction percentage.

The math is based on Xona's published specifications (see specs.py).
"""

from app.detection.interfaces.models import ZoneData
from app.pulsar.interfaces.specs import (
    AREA_REDUCTION_PCT,
    RADIUS_REDUCTION_FACTOR,
    SIGNAL_ADVANTAGE_L1_DB,
)


def compute_pulsar_mitigation(zone: ZoneData) -> ZoneData:
    """
    Compute Pulsar mitigation metrics for a single interference zone.

    Updates the zone's Pulsar fields:
        - gps_jam_radius_km: Original GPS jamming radius (= zone.radius_km).
        - pulsar_jam_radius_km: zone.radius_km / 6.3 (reduced by Pulsar).
        - spoofing_eliminated: True if zone contains spoofing events.
        - signal_advantage_db: 22.5 dB (vs GPS L1).
        - area_reduction_pct: 97.5% (conservative, using L5 spec).

    Args:
        zone: A ZoneData instance from the clustering stage.

    Returns:
        Updated ZoneData with Pulsar mitigation fields populated.
    """
    return zone.model_copy(update={
        "gps_jam_radius_km": zone.radius_km,
        "pulsar_jam_radius_km": zone.radius_km / RADIUS_REDUCTION_FACTOR,
        "spoofing_eliminated": zone.event_type in ("spoofing", "mixed"),
        "signal_advantage_db": SIGNAL_ADVANTAGE_L1_DB,
        "area_reduction_pct": AREA_REDUCTION_PCT,
    })
