"""
Geographic utility functions for the detection pipeline.

Provides haversine distance, bearing computation, and angular difference
calculations used by all 6 anomaly detectors. All formulas use the
WGS-84 Earth radius (6,371,000 m).

These are pure functions with no side effects or external dependencies
beyond the math standard library.
"""

from math import atan2, cos, radians, sin, sqrt

# Earth radius in meters (WGS-84 mean).
EARTH_RADIUS_M = 6_371_000


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute the great-circle distance between two WGS-84 coordinates.

    Uses the Haversine formula for accuracy on a spherical Earth model.

    Args:
        lat1: Latitude of point 1 in degrees.
        lon1: Longitude of point 1 in degrees.
        lat2: Latitude of point 2 in degrees.
        lon2: Longitude of point 2 in degrees.

    Returns:
        Distance in meters between the two points.
    """
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    dphi = radians(lat2 - lat1)
    dlam = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlam / 2) ** 2
    return EARTH_RADIUS_M * 2 * atan2(sqrt(a), sqrt(1 - a))


def compute_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute the initial bearing from point 1 to point 2.

    Returns the forward azimuth (compass bearing) in degrees [0, 360).

    Args:
        lat1: Latitude of point 1 in degrees.
        lon1: Longitude of point 1 in degrees.
        lat2: Latitude of point 2 in degrees.
        lon2: Longitude of point 2 in degrees.

    Returns:
        Bearing in degrees, [0, 360).
    """
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    dlam = radians(lon2 - lon1)
    x = sin(dlam) * cos(phi2)
    y = cos(phi1) * sin(phi2) - sin(phi1) * cos(phi2) * cos(dlam)
    from math import degrees

    return (degrees(atan2(x, y)) + 360) % 360


def angular_difference(a: float, b: float) -> float:
    """
    Compute the smallest angle between two bearings.

    Handles wraparound at 0/360 degrees correctly.

    Args:
        a: First bearing in degrees.
        b: Second bearing in degrees.

    Returns:
        Angular difference in degrees, [0, 180].
    """
    diff = abs(a - b) % 360
    return min(diff, 360 - diff)
