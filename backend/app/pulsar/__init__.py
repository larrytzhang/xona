"""
GPS Shield — Pulsar Mitigation Modeler.

Computes per-zone Pulsar impact metrics (radius reduction, spoofing
elimination, signal advantage). Public interface only — import from
here, not from pulsar.internal.

Re-exports:
    compute_pulsar_mitigation, and all spec constants.
"""

from app.pulsar.interfaces.specs import (
    AREA_REDUCTION_PCT,
    GPS_L1_SIGNAL_DBW,
    GPS_L5_SIGNAL_DBW,
    PULSAR_SIGNAL_DBW,
    RADIUS_REDUCTION_FACTOR,
    SIGNAL_ADVANTAGE_L1_DB,
    SIGNAL_ADVANTAGE_L5_DB,
)
from app.pulsar.internal.modeler import compute_pulsar_mitigation

__all__ = [
    "compute_pulsar_mitigation",
    "GPS_L1_SIGNAL_DBW",
    "GPS_L5_SIGNAL_DBW",
    "PULSAR_SIGNAL_DBW",
    "SIGNAL_ADVANTAGE_L1_DB",
    "SIGNAL_ADVANTAGE_L5_DB",
    "RADIUS_REDUCTION_FACTOR",
    "AREA_REDUCTION_PCT",
]
