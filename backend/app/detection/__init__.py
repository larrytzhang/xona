"""
GPS Shield — Anomaly Detection Pipeline.

Public interface for the detection engine. All external consumers should
import from this package or from detection.interfaces — never from
detection.internal directly.

Re-exports:
    Data models: AircraftState, AnomalyFlag, DetectionResult, ClassifiedAnomaly, ZoneData
    Pipeline: AnomalyPipeline
    Zone utilities: KNOWN_ZONES, REGION_NAMES, ZONES_BY_ID, classify_zone
"""

from app.detection.interfaces.models import (
    AircraftState,
    AnomalyFlag,
    ClassifiedAnomaly,
    DetectionResult,
    ZoneData,
)
from app.detection.internal.pipeline import AnomalyPipeline
from app.detection.internal.zones import (
    KNOWN_ZONES,
    REGION_NAMES,
    ZONES_BY_ID,
    classify_zone,
)

__all__ = [
    "AircraftState",
    "AnomalyFlag",
    "AnomalyPipeline",
    "ClassifiedAnomaly",
    "DetectionResult",
    "KNOWN_ZONES",
    "REGION_NAMES",
    "ZONES_BY_ID",
    "ZoneData",
    "classify_zone",
]
