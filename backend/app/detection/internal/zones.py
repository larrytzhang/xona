"""
Known GPS interference zone definitions.

Defines the 7 known interference regions and provides a function to
classify any lat/lon coordinate to its nearest known zone. Used by
the classifier and pipeline to tag anomaly events with a region.

Zone data is from publicly available GPS interference reporting.
"""

from dataclasses import dataclass

from app.detection.internal.geo import haversine


@dataclass(frozen=True)
class KnownZone:
    """
    A known geographic region of GPS interference.

    Attributes:
        zone_id: Unique string identifier for the zone.
        name: Human-readable display name.
        center_lat: Zone center latitude in degrees.
        center_lon: Zone center longitude in degrees.
        radius_km: Approximate interference radius in km.
        known_source: Brief description of the interference source.
    """

    zone_id: str
    name: str
    center_lat: float
    center_lon: float
    radius_km: float
    known_source: str


# The 7 known interference zones from Part 7.12.
KNOWN_ZONES: list[KnownZone] = [
    KnownZone("baltic_sea", "Baltic Sea / Eastern Europe", 57.0, 22.0, 800, "Russian EW systems"),
    KnownZone("eastern_med", "Eastern Mediterranean", 35.0, 34.0, 600, "Multiple state actors"),
    KnownZone("persian_gulf", "Persian Gulf", 26.5, 54.0, 500, "Iranian GPS denial"),
    KnownZone("red_sea", "Red Sea / Gulf of Aden", 15.0, 42.0, 600, "Houthi-linked operations"),
    KnownZone("black_sea", "Black Sea", 43.0, 35.0, 500, "Russian EW"),
    KnownZone("ukraine_frontline", "Ukraine Frontline", 49.0, 36.0, 400, "Active conflict EW"),
    KnownZone("south_china_sea", "South China Sea", 15.0, 115.0, 700, "State-level interference"),
]

# Lookup dict for quick access by zone_id.
ZONES_BY_ID: dict[str, KnownZone] = {z.zone_id: z for z in KNOWN_ZONES}

# Region display names for the frontend.
REGION_NAMES: dict[str, str] = {z.zone_id: z.name for z in KNOWN_ZONES}
REGION_NAMES["other"] = "Other / Unknown"


def classify_zone(lat: float, lon: float) -> str:
    """
    Classify a lat/lon coordinate to its nearest known interference zone.

    Computes haversine distance from the given point to each known zone
    center and returns the zone_id of the closest zone within its radius.
    Returns 'other' if no zone is within range.

    Args:
        lat: Latitude in degrees.
        lon: Longitude in degrees.

    Returns:
        Zone ID string (e.g., 'baltic_sea') or 'other'.
    """
    best_zone = "other"
    best_distance = float("inf")

    for zone in KNOWN_ZONES:
        dist_m = haversine(lat, lon, zone.center_lat, zone.center_lon)
        dist_km = dist_m / 1000.0
        if dist_km <= zone.radius_km and dist_km < best_distance:
            best_distance = dist_km
            best_zone = zone.zone_id

    return best_zone
