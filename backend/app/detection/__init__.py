"""
GPS Shield — Anomaly Detection Pipeline.

Public interface for the detection engine. All external consumers should
import from this package or from detection.interfaces — never from
detection.internal directly.

Re-exports:
    AircraftState, AnomalyFlag, DetectionResult, ClassifiedAnomaly, ZoneData
"""

from app.detection.interfaces.models import (
    AircraftState,
    AnomalyFlag,
    ClassifiedAnomaly,
    DetectionResult,
    ZoneData,
)

__all__ = [
    "AircraftState",
    "AnomalyFlag",
    "ClassifiedAnomaly",
    "DetectionResult",
    "ZoneData",
]
