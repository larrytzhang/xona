"""
Detection pipeline public data contracts.

All Pydantic models used for inter-module communication within the
detection pipeline. These define the shape of data flowing between
ingestion -> detectors -> classifier -> scorer -> clusterer -> zones.

Every module in the detection package imports these models from here
(via detection.interfaces or detection.__init__). No module should
define its own ad-hoc dicts for passing detection data.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AircraftState(BaseModel):
    """
    A cleaned aircraft state vector from OpenSky Network.

    Represents one aircraft at one moment in time, after cleaning
    rules from Part 7.2 have been applied.

    Attributes:
        icao24: Unique aircraft hex identifier (6 chars).
        callsign: Flight callsign (may be empty).
        latitude: WGS-84 latitude in degrees.
        longitude: WGS-84 longitude in degrees.
        baro_altitude: Barometric altitude in meters, or None.
        geo_altitude: GPS altitude in meters, or None.
        velocity: Ground speed in m/s, or None.
        true_track: Heading in degrees [0, 360), or None.
        vertical_rate: Vertical speed in m/s (positive = climbing), or None.
        on_ground: Whether the aircraft is on the ground.
        timestamp: Unix epoch seconds of the position report.
        last_contact: Unix epoch seconds of the last ADS-B message.
        altitude_discrepancy: geo_altitude - baro_altitude, computed during cleaning (Part 7.2 rule 8).
    """

    icao24: str
    callsign: str = ""
    latitude: float
    longitude: float
    baro_altitude: Optional[float] = None
    geo_altitude: Optional[float] = None
    velocity: Optional[float] = None
    true_track: Optional[float] = None
    vertical_rate: Optional[float] = None
    on_ground: bool = False
    timestamp: int = 0
    last_contact: int = 0
    altitude_discrepancy: Optional[float] = None


class AnomalyFlag(BaseModel):
    """
    A single flag raised by one of the 6 anomaly detectors.

    Each detector can raise zero or more flags per aircraft per snapshot.
    Flags carry the detector name, measured value, threshold exceeded,
    confidence score, and a human-readable description.

    Attributes:
        detector: Name of the detector that raised this flag
                  (e.g., 'velocity', 'position_jump', 'altitude', 'heading').
        value: The measured value that triggered the flag.
        threshold: The threshold that was exceeded.
        confidence: Confidence score from 0.0 to 1.0.
        detail: Human-readable description of the anomaly.
    """

    detector: str
    value: float
    threshold: float
    confidence: float
    detail: str


class DetectionResult(BaseModel):
    """
    The combined output of all detectors for a single aircraft.

    Contains the aircraft state, all raised flags, whether a signal
    loss was detected, and cluster membership info (set by the clusterer).

    Attributes:
        aircraft: The aircraft state that was analyzed.
        flags: List of anomaly flags from all detectors.
        has_signal_loss: Whether this aircraft stopped reporting (signal loss).
        is_clustered: Whether this detection belongs to a spatial cluster.
        cluster_id: Cluster identifier if clustered, else None.
        consecutive_anomalous: Number of consecutive anomalous states for this aircraft.
    """

    aircraft: AircraftState
    flags: list[AnomalyFlag] = []
    has_signal_loss: bool = False
    is_clustered: bool = False
    cluster_id: Optional[int] = None
    consecutive_anomalous: int = 0


class ClassifiedAnomaly(BaseModel):
    """
    A detection result after classification and severity scoring.

    Extends DetectionResult with the anomaly type classification
    and severity score.

    Attributes:
        detection: The underlying detection result with flags.
        anomaly_type: Classification: 'spoofing', 'jamming', or 'anomaly'.
        severity: Severity score 0-100.
        severity_label: Human-readable severity label.
        region: Known interference region identifier.
    """

    detection: DetectionResult
    anomaly_type: str
    severity: int
    severity_label: str
    region: str


class ZoneData(BaseModel):
    """
    An interference zone produced by the clustering stage.

    Represents a geographic area where multiple anomalous aircraft
    have been detected, with Pulsar mitigation calculations applied.

    Attributes:
        center_lat: Zone center latitude.
        center_lon: Zone center longitude.
        radius_km: Estimated interference radius in km.
        event_type: 'spoofing', 'jamming', or 'mixed'.
        severity: Maximum severity of contained anomalies.
        affected_aircraft: Number of aircraft in the zone.
        start_time: Earliest detection timestamp.
        end_time: Latest detection timestamp, or None if active.
        region: Known interference region.
        anomalies: List of classified anomalies in this zone.
        gps_jam_radius_km: GPS jamming effective radius.
        pulsar_jam_radius_km: Reduced radius under Pulsar.
        spoofing_eliminated: Whether Pulsar eliminates spoofing here.
        signal_advantage_db: Pulsar signal advantage in dB.
        area_reduction_pct: Area reduction percentage with Pulsar.
    """

    center_lat: float
    center_lon: float
    radius_km: float
    event_type: str
    severity: int
    affected_aircraft: int
    start_time: datetime
    end_time: Optional[datetime] = None
    region: str
    anomalies: list[ClassifiedAnomaly] = []
    gps_jam_radius_km: Optional[float] = None
    pulsar_jam_radius_km: Optional[float] = None
    spoofing_eliminated: bool = False
    signal_advantage_db: Optional[float] = None
    area_reduction_pct: Optional[float] = None
