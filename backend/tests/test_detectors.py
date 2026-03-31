"""
Tests for the GPS Shield detection pipeline components.

Tests geo utilities, known zone classification, and the sliding window
manager. Later steps will add detector, classifier, and scorer tests.
"""

from app.detection.interfaces.models import AircraftState
from app.detection.internal.geo import angular_difference, compute_bearing, haversine
from app.detection.internal.window import StateWindowManager
from app.detection.internal.zones import classify_zone


# =========================================================================
# Geo utilities
# =========================================================================


class TestHaversine:
    """Tests for the haversine distance function."""

    def test_nyc_to_london(self):
        """
        NYC (40.7128, -74.0060) to London (51.5074, -0.1278) is ~5,570 km.

        Verifies haversine returns a value within 1% of known distance.
        """
        dist = haversine(40.7128, -74.0060, 51.5074, -0.1278)
        assert abs(dist - 5_570_000) < 60_000  # within 60 km (~1%)

    def test_same_point_returns_zero(self):
        """
        Distance from a point to itself should be zero.
        """
        dist = haversine(45.0, 90.0, 45.0, 90.0)
        assert dist == 0.0

    def test_antipodal_points(self):
        """
        Distance between antipodal points should be ~half Earth circumference.
        ~20,015 km (pi * R).
        """
        dist = haversine(0.0, 0.0, 0.0, 180.0)
        assert abs(dist - 20_015_000) < 100_000  # within 100 km

    def test_short_distance(self):
        """
        Two points ~111 km apart (1 degree latitude at equator).
        """
        dist = haversine(0.0, 0.0, 1.0, 0.0)
        assert abs(dist - 111_195) < 500  # within 500 m


class TestComputeBearing:
    """Tests for the initial bearing computation."""

    def test_due_north(self):
        """
        Bearing from equator going straight north should be ~0 degrees.
        """
        bearing = compute_bearing(0.0, 0.0, 10.0, 0.0)
        assert abs(bearing - 0.0) < 1.0

    def test_due_east(self):
        """
        Bearing from equator going straight east should be ~90 degrees.
        """
        bearing = compute_bearing(0.0, 0.0, 0.0, 10.0)
        assert abs(bearing - 90.0) < 1.0

    def test_due_south(self):
        """
        Bearing going straight south should be ~180 degrees.
        """
        bearing = compute_bearing(10.0, 0.0, 0.0, 0.0)
        assert abs(bearing - 180.0) < 1.0

    def test_due_west(self):
        """
        Bearing going straight west should be ~270 degrees.
        """
        bearing = compute_bearing(0.0, 10.0, 0.0, 0.0)
        assert abs(bearing - 270.0) < 1.0


class TestAngularDifference:
    """Tests for the angular difference function."""

    def test_zero_difference(self):
        """Same bearing should have 0 difference."""
        assert angular_difference(90.0, 90.0) == 0.0

    def test_opposite_bearings(self):
        """Opposite bearings (0 and 180) should differ by 180."""
        assert angular_difference(0.0, 180.0) == 180.0

    def test_wraparound(self):
        """350 and 10 degrees should differ by 20 (wraparound)."""
        assert abs(angular_difference(350.0, 10.0) - 20.0) < 0.01

    def test_large_values(self):
        """Should handle values > 360 correctly."""
        assert abs(angular_difference(370.0, 10.0) - 0.0) < 0.01


# =========================================================================
# Zone classification
# =========================================================================


class TestClassifyZone:
    """Tests for the known zone classification function."""

    def test_baltic_sea_center(self):
        """Point at Baltic Sea zone center should classify as baltic_sea."""
        assert classify_zone(57.0, 22.0) == "baltic_sea"

    def test_persian_gulf_center(self):
        """Point at Persian Gulf center should classify as persian_gulf."""
        assert classify_zone(26.5, 54.0) == "persian_gulf"

    def test_open_ocean(self):
        """Point in mid-Pacific should classify as 'other'."""
        assert classify_zone(0.0, -150.0) == "other"

    def test_near_zone_boundary(self):
        """Point near but within Baltic zone radius should still match."""
        assert classify_zone(57.0, 28.0) == "baltic_sea"

    def test_south_china_sea(self):
        """Point at South China Sea center should classify correctly."""
        assert classify_zone(15.0, 115.0) == "south_china_sea"


# =========================================================================
# State window manager
# =========================================================================


class TestStateWindowManager:
    """Tests for the sliding window manager."""

    def _make_state(self, icao: str = "ABC123", ts: int = 1000,
                    lat: float = 50.0, lon: float = 10.0) -> AircraftState:
        """
        Create a test aircraft state with the given parameters.

        Args:
            icao: Aircraft identifier.
            ts: Unix timestamp.
            lat: Latitude in degrees.
            lon: Longitude in degrees.

        Returns:
            AircraftState instance.
        """
        return AircraftState(
            icao24=icao, latitude=lat, longitude=lon,
            timestamp=ts, last_contact=ts,
        )

    def test_first_state_returns_none(self):
        """First state for an aircraft should return None (no previous)."""
        wm = StateWindowManager()
        prev = wm.update(self._make_state())
        assert prev is None

    def test_second_state_returns_first(self):
        """Second state should return the first as previous."""
        wm = StateWindowManager()
        s1 = self._make_state(ts=1000)
        s2 = self._make_state(ts=1010)
        wm.update(s1)
        prev = wm.update(s2)
        assert prev is not None
        assert prev.timestamp == 1000

    def test_window_prunes_old_states(self):
        """States older than WINDOW_MAX_AGE should be pruned."""
        wm = StateWindowManager()
        # Add states spanning 400 seconds (> 300s max age).
        for t in range(0, 400, 10):
            wm.update(self._make_state(ts=t))
        window = wm.get_window("ABC123")
        # All states should be within 300s of the latest (390).
        for s in window:
            assert s.timestamp >= 400 - 300 - 10  # allow for the last state

    def test_cleanup_stale_removes_old_aircraft(self):
        """Aircraft not seen for STALE_THRESHOLD should be cleaned up."""
        wm = StateWindowManager()
        wm.update(self._make_state(icao="OLD1", ts=1000))
        wm.update(self._make_state(icao="NEW1", ts=2000))
        # Current time is 2000, OLD1 last seen at 1000 (1000s ago > 600s threshold).
        removed = wm.cleanup_stale(2000)
        assert "OLD1" in removed
        assert "NEW1" not in removed

    def test_anomaly_count_tracking(self):
        """Anomaly count should increment and reset correctly."""
        wm = StateWindowManager()
        wm.update(self._make_state())
        assert wm.get_anomaly_count("ABC123") == 0
        wm.increment_anomaly_count("ABC123")
        wm.increment_anomaly_count("ABC123")
        assert wm.get_anomaly_count("ABC123") == 2
        wm.reset_anomaly_count("ABC123")
        assert wm.get_anomaly_count("ABC123") == 0
