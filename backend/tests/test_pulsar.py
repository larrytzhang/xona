"""
Tests for the Pulsar mitigation modeler.

Verifies that Pulsar impact calculations match Xona's published specs:
    - 6.3x radius reduction (vs L5).
    - 97.5% area reduction.
    - 100% spoofing elimination via cryptographic authentication.
    - 22.5 dB signal advantage vs GPS L1.
"""

from datetime import datetime, timezone

from app.detection.interfaces.models import ZoneData
from app.pulsar import compute_pulsar_mitigation
from app.pulsar.interfaces.specs import (
    AREA_REDUCTION_PCT,
    RADIUS_REDUCTION_FACTOR,
    SIGNAL_ADVANTAGE_L1_DB,
)


def _make_zone(radius_km: float = 150.0, event_type: str = "spoofing") -> ZoneData:
    """
    Create a test ZoneData with the given radius and event type.

    Args:
        radius_km: Zone radius in kilometers.
        event_type: 'spoofing', 'jamming', or 'mixed'.

    Returns:
        ZoneData instance.
    """
    return ZoneData(
        center_lat=57.0,
        center_lon=22.0,
        radius_km=radius_km,
        event_type=event_type,
        severity=65,
        affected_aircraft=10,
        start_time=datetime(2026, 3, 30, 12, 0, tzinfo=timezone.utc),
        region="baltic_sea",
    )


class TestPulsarMitigation:
    """Tests for the compute_pulsar_mitigation function."""

    def test_radius_reduction(self):
        """150 km GPS radius -> ~23.8 km Pulsar radius (/ 6.3)."""
        zone = _make_zone(radius_km=150.0)
        result = compute_pulsar_mitigation(zone)
        expected = 150.0 / RADIUS_REDUCTION_FACTOR
        assert abs(result.pulsar_jam_radius_km - expected) < 0.1
        assert abs(result.pulsar_jam_radius_km - 23.8) < 0.1

    def test_gps_radius_preserved(self):
        """GPS jam radius should equal original zone radius."""
        zone = _make_zone(radius_km=200.0)
        result = compute_pulsar_mitigation(zone)
        assert result.gps_jam_radius_km == 200.0

    def test_spoofing_zone_eliminated(self):
        """Spoofing zone -> spoofing_eliminated = True."""
        zone = _make_zone(event_type="spoofing")
        result = compute_pulsar_mitigation(zone)
        assert result.spoofing_eliminated is True

    def test_mixed_zone_eliminated(self):
        """Mixed zone (spoofing + jamming) -> spoofing_eliminated = True."""
        zone = _make_zone(event_type="mixed")
        result = compute_pulsar_mitigation(zone)
        assert result.spoofing_eliminated is True

    def test_jamming_zone_not_eliminated(self):
        """Jamming-only zone -> spoofing_eliminated = False."""
        zone = _make_zone(event_type="jamming")
        result = compute_pulsar_mitigation(zone)
        assert result.spoofing_eliminated is False

    def test_signal_advantage(self):
        """Signal advantage should be 22.5 dB (vs L1)."""
        zone = _make_zone()
        result = compute_pulsar_mitigation(zone)
        assert result.signal_advantage_db == SIGNAL_ADVANTAGE_L1_DB
        assert result.signal_advantage_db == 22.5

    def test_area_reduction(self):
        """Area reduction should be 97.5%."""
        zone = _make_zone()
        result = compute_pulsar_mitigation(zone)
        assert result.area_reduction_pct == AREA_REDUCTION_PCT
        assert result.area_reduction_pct == 97.5

    def test_original_zone_fields_preserved(self):
        """Non-Pulsar fields should remain unchanged."""
        zone = _make_zone(radius_km=120.0, event_type="spoofing")
        result = compute_pulsar_mitigation(zone)
        assert result.center_lat == 57.0
        assert result.center_lon == 22.0
        assert result.radius_km == 120.0
        assert result.severity == 65
        assert result.affected_aircraft == 10
        assert result.region == "baltic_sea"
