"""
DBSCAN spatial clustering and signal loss detection.

Groups anomalous aircraft detections into geographic clusters
(interference zones) using DBSCAN, and detects coordinated signal
loss events that indicate regional jamming.

Constants from Part 7.8 and 7.9:
    CLUSTER_RADIUS_KM = 150 km (eps = 150 / 6371)
    CLUSTER_MIN_AIRCRAFT = 3
    SIGNAL_LOSS_TIMEOUT = 30 seconds
    SIGNAL_LOSS_MIN_COUNT = 5 aircraft
    SIGNAL_LOSS_RADIUS_KM = 200 km
"""

from datetime import datetime, timezone
from math import radians
from typing import Optional

import numpy as np
from sklearn.cluster import DBSCAN

from app.detection.interfaces.models import (
    AircraftState,
    ClassifiedAnomaly,
    ZoneData,
)
from app.detection.internal.geo import haversine
from app.detection.internal.zones import classify_zone

# DBSCAN parameters from Part 7.8.
CLUSTER_RADIUS_KM = 150
CLUSTER_EPS = CLUSTER_RADIUS_KM / 6371  # radians
CLUSTER_MIN_AIRCRAFT = 3

# Signal loss parameters from Part 7.9.
SIGNAL_LOSS_TIMEOUT = 30       # seconds
SIGNAL_LOSS_MIN_COUNT = 5      # aircraft
SIGNAL_LOSS_RADIUS_KM = 200    # km


def cluster_anomalies(
    anomalies: list[ClassifiedAnomaly],
) -> list[list[ClassifiedAnomaly]]:
    """
    Group classified anomalies into spatial clusters using DBSCAN.

    Runs DBSCAN with haversine metric on the lat/lon coordinates
    of all provided anomalies. Returns a list of clusters, where
    each cluster is a list of anomalies belonging to the same group.
    Anomalies not assigned to any cluster are returned individually
    as single-element lists.

    Args:
        anomalies: List of classified anomaly events to cluster.

    Returns:
        List of clusters (each cluster is a list of ClassifiedAnomaly).
        Single anomalies not in any cluster are each in their own list.
    """
    if len(anomalies) < CLUSTER_MIN_AIRCRAFT:
        return [[a] for a in anomalies]

    # Prepare coordinate matrix in radians for haversine metric.
    coords = np.array([
        [radians(a.detection.aircraft.latitude), radians(a.detection.aircraft.longitude)]
        for a in anomalies
    ])

    clustering = DBSCAN(
        eps=CLUSTER_EPS,
        min_samples=CLUSTER_MIN_AIRCRAFT,
        metric="haversine",
    ).fit(coords)

    # Group by cluster label.
    clusters: dict[int, list[ClassifiedAnomaly]] = {}
    noise: list[ClassifiedAnomaly] = []

    for idx, label in enumerate(clustering.labels_):
        if label == -1:
            noise.append(anomalies[idx])
        else:
            clusters.setdefault(label, []).append(anomalies[idx])

    result = list(clusters.values())
    # Add noise points as individual "clusters".
    for a in noise:
        result.append([a])

    return result


def detect_signal_loss(
    current_icao24s: set[str],
    previous_icao24s: set[str],
    last_positions: dict[str, AircraftState],
    snapshot_time: int,
) -> list[ZoneData]:
    """
    Detect coordinated signal loss events indicating regional jamming.

    Identifies aircraft that stopped reporting between two consecutive
    snapshots. If 5+ aircraft within 200 km all disappeared within
    30 seconds, classifies as a jamming event.

    Args:
        current_icao24s: Set of icao24s in the current snapshot.
        previous_icao24s: Set of icao24s in the previous snapshot.
        last_positions: Dict mapping icao24 -> last known AircraftState.
        snapshot_time: Unix timestamp of the current snapshot.

    Returns:
        List of ZoneData representing detected signal loss zones.
    """
    # Find aircraft that disappeared.
    disappeared = previous_icao24s - current_icao24s
    if len(disappeared) < SIGNAL_LOSS_MIN_COUNT:
        return []

    # Filter to recent disappearances (within SIGNAL_LOSS_TIMEOUT).
    recent_lost: list[AircraftState] = []
    for icao in disappeared:
        state = last_positions.get(icao)
        if state and (snapshot_time - state.timestamp) <= SIGNAL_LOSS_TIMEOUT:
            recent_lost.append(state)

    if len(recent_lost) < SIGNAL_LOSS_MIN_COUNT:
        return []

    # Cluster the lost aircraft positions using DBSCAN.
    coords = np.array([
        [radians(s.latitude), radians(s.longitude)]
        for s in recent_lost
    ])

    signal_eps = SIGNAL_LOSS_RADIUS_KM / 6371
    clustering = DBSCAN(
        eps=signal_eps,
        min_samples=SIGNAL_LOSS_MIN_COUNT,
        metric="haversine",
    ).fit(coords)

    zones: list[ZoneData] = []
    cluster_labels = set(clustering.labels_)
    cluster_labels.discard(-1)

    for label in cluster_labels:
        members = [recent_lost[i] for i, lbl in enumerate(clustering.labels_) if lbl == label]
        zone = _create_signal_loss_zone(members, snapshot_time)
        if zone:
            zones.append(zone)

    return zones


def _create_signal_loss_zone(
    members: list[AircraftState],
    snapshot_time: int,
) -> Optional[ZoneData]:
    """
    Create a ZoneData from a cluster of signal-loss aircraft.

    Computes the center, radius, and region for the zone.

    Args:
        members: List of AircraftState for aircraft that lost signal.
        snapshot_time: Unix timestamp of the detection.

    Returns:
        ZoneData instance, or None if cluster is invalid.
    """
    if not members:
        return None

    lats = [s.latitude for s in members]
    lons = [s.longitude for s in members]
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)

    # Compute radius as max distance from center.
    max_dist = 0.0
    for s in members:
        d = haversine(center_lat, center_lon, s.latitude, s.longitude)
        max_dist = max(max_dist, d)
    radius_km = max(max_dist / 1000, 50.0)  # Minimum 50 km radius.

    region = classify_zone(center_lat, center_lon)
    ts = datetime.fromtimestamp(snapshot_time, tz=timezone.utc)

    return ZoneData(
        center_lat=center_lat,
        center_lon=center_lon,
        radius_km=radius_km,
        event_type="jamming",
        severity=60,  # Default for signal loss; will be refined by scorer.
        affected_aircraft=len(members),
        start_time=ts,
        region=region,
    )


def build_zones_from_clusters(
    clusters: list[list[ClassifiedAnomaly]],
    snapshot_time: int,
) -> list[ZoneData]:
    """
    Convert anomaly clusters into interference ZoneData objects.

    Each cluster with 3+ aircraft becomes a zone. Computes center,
    radius, severity, event type, and region.

    Args:
        clusters: List of clusters (each a list of ClassifiedAnomaly).
        snapshot_time: Unix timestamp of the detection.

    Returns:
        List of ZoneData representing interference zones.
    """
    zones: list[ZoneData] = []

    for cluster in clusters:
        if len(cluster) < CLUSTER_MIN_AIRCRAFT:
            continue

        lats = [a.detection.aircraft.latitude for a in cluster]
        lons = [a.detection.aircraft.longitude for a in cluster]
        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)

        # Radius: max distance from center.
        max_dist = 0.0
        for a in cluster:
            d = haversine(
                center_lat, center_lon,
                a.detection.aircraft.latitude, a.detection.aircraft.longitude,
            )
            max_dist = max(max_dist, d)
        radius_km = max(max_dist / 1000, 20.0)

        # Aggregate severity and type.
        max_severity = max(a.severity for a in cluster)
        types = {a.anomaly_type for a in cluster}
        if "spoofing" in types and "jamming" in types:
            event_type = "mixed"
        elif "spoofing" in types:
            event_type = "spoofing"
        elif "jamming" in types:
            event_type = "jamming"
        else:
            event_type = "mixed"  # uncertain cluster, multiple possible types

        region = classify_zone(center_lat, center_lon)
        ts = datetime.fromtimestamp(snapshot_time, tz=timezone.utc)

        zones.append(ZoneData(
            center_lat=center_lat,
            center_lon=center_lon,
            radius_km=radius_km,
            event_type=event_type,
            severity=max_severity,
            affected_aircraft=len(cluster),
            start_time=ts,
            region=region,
            anomalies=cluster,
        ))

    return zones
