"""
Severity scoring for classified anomaly events.

Computes a 0-100 severity score using the weighted formula from
Part 7.11 of the master plan, plus a human-readable severity label.

The score factors in:
    - Maximum flag confidence (35%)
    - Number of flags (15%)
    - Cluster membership (25%)
    - Persistence / consecutive anomalous states (15%)
    - Altitude risk level (10%)
"""

from typing import Optional

from app.detection.interfaces.models import AnomalyFlag

# Severity label breakpoints from Part 7.11.
SEVERITY_LABELS = [
    (20, "low"),
    (40, "moderate"),
    (60, "elevated"),
    (80, "high"),
    (101, "critical"),
]


def _get_severity_label(severity: int) -> str:
    """
    Map a 0-100 severity score to a human-readable label.

    Breakpoints:
        0-19: low, 20-39: moderate, 40-59: elevated,
        60-79: high, 80-100: critical.

    Args:
        severity: Integer severity score (0-100).

    Returns:
        Severity label string.
    """
    for threshold, label in SEVERITY_LABELS:
        if severity < threshold:
            return label
    return "critical"


def _altitude_risk(altitude: Optional[float]) -> float:
    """
    Compute altitude risk factor based on flight phase.

    Low altitude (approach/departure) is highest risk. Cruise is lowest.

    Args:
        altitude: Aircraft altitude in meters, or None.

    Returns:
        Risk factor 0.0-1.0.
    """
    if altitude is None:
        return 0.6
    if altitude < 3000:
        return 0.8  # approach / departure — high risk
    if altitude <= 10000:
        return 0.5  # transition
    return 0.3  # cruise — lower risk


def compute_severity(
    flags: list[AnomalyFlag],
    is_clustered: bool = False,
    cluster_size: int = 0,
    consecutive_anomalous: int = 0,
    altitude: Optional[float] = None,
) -> tuple[int, str]:
    """
    Compute severity score (0-100) and label for an anomaly event.

    Formula (Part 7.11):
        severity = clamp(0, 100,
            0.35 * max_flag_confidence * 100
          + 0.15 * flag_count_score * 100
          + 0.25 * cluster_factor * 100
          + 0.15 * persistence_factor * 100
          + 0.10 * altitude_risk * 100
        )

    Args:
        flags: List of anomaly flags from all detectors.
        is_clustered: Whether this event is part of a spatial cluster.
        cluster_size: Number of aircraft in the cluster (0 if not clustered).
        consecutive_anomalous: Count of consecutive anomalous states.
        altitude: Aircraft altitude in meters, or None.

    Returns:
        Tuple of (severity_score, severity_label).
    """
    if not flags:
        return (0, "low")

    # Component calculations.
    max_flag_confidence = max(f.confidence for f in flags)
    flag_count_score = min(1.0, len(flags) / 5.0)
    cluster_factor = 0.0 if not is_clustered else min(1.0, cluster_size / 20)
    persistence_factor = min(1.0, consecutive_anomalous / 10)
    alt_risk = _altitude_risk(altitude)

    # Weighted sum.
    raw = (
        0.35 * max_flag_confidence * 100
        + 0.15 * flag_count_score * 100
        + 0.25 * cluster_factor * 100
        + 0.15 * persistence_factor * 100
        + 0.10 * alt_risk * 100
    )

    severity = max(0, min(100, int(round(raw))))
    label = _get_severity_label(severity)

    return (severity, label)
