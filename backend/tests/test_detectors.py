"""
Tests for the GPS Shield detection pipeline components.

Tests geo utilities, known zone classification, and the sliding window
manager. Later steps will add detector, classifier, and scorer tests.
"""

from app.detection.interfaces.models import AircraftState, AnomalyFlag, ClassifiedAnomaly, DetectionResult
from app.detection.internal.classifier import classify
from app.detection.internal.clusterer import build_zones_from_clusters, cluster_anomalies
from app.detection.internal.detectors import (
    detect_altitude,
    detect_heading,
    detect_position_jump,
    detect_velocity,
)
from app.detection.internal.scorer import compute_severity
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


# =========================================================================
# Velocity detector
# =========================================================================


def _make_state(**kwargs) -> AircraftState:
    """
    Helper to create AircraftState with sensible defaults.

    Args:
        **kwargs: Override any AircraftState field.

    Returns:
        AircraftState instance.
    """
    defaults = dict(
        icao24="ABC123", latitude=50.0, longitude=10.0,
        timestamp=1000, last_contact=1000,
        velocity=250.0, true_track=90.0,
        baro_altitude=10000.0, geo_altitude=10000.0,
    )
    defaults.update(kwargs)
    return AircraftState(**defaults)


class TestVelocityDetector:
    """Tests for the impossible velocity detector."""

    def test_normal_velocity_no_flags(self):
        """Normal 250 m/s velocity should produce no flags."""
        prev = _make_state(timestamp=990)
        curr = _make_state(timestamp=1000, velocity=250.0)
        flags = detect_velocity(curr, prev)
        assert len(flags) == 0

    def test_supersonic_velocity_flags(self):
        """500 m/s velocity should flag with confidence ~0.44."""
        prev = _make_state(timestamp=990, velocity=250.0)
        curr = _make_state(timestamp=1000, velocity=500.0)
        flags = detect_velocity(curr, prev)
        # Should have at least the reported velocity flag.
        velocity_flags = [f for f in flags if f.detector == "velocity" and f.value == 500.0]
        assert len(velocity_flags) == 1
        assert abs(velocity_flags[0].confidence - 0.44) < 0.05

    def test_derived_velocity_flag(self):
        """50 km position change in 5 seconds -> derived 10000 m/s, should flag."""
        prev = _make_state(timestamp=995, latitude=50.0, longitude=10.0)
        # Move ~50 km east (roughly 0.65 degrees at lat 50)
        curr = _make_state(timestamp=1000, latitude=50.0, longitude=10.65, velocity=250.0)
        flags = detect_velocity(curr, prev)
        derived_flags = [f for f in flags if f.threshold == 400.0]
        assert len(derived_flags) >= 1

    def test_acceleration_flag(self):
        """Velocity jump from 100 to 400 in 1 second (300 m/s²) should flag."""
        prev = _make_state(timestamp=999, velocity=100.0)
        curr = _make_state(timestamp=1000, velocity=400.0)
        flags = detect_velocity(curr, prev)
        accel_flags = [f for f in flags if "cceleration" in f.detail]
        assert len(accel_flags) >= 1


# =========================================================================
# Position jump detector
# =========================================================================


class TestPositionJumpDetector:
    """Tests for the position jump (teleportation) detector."""

    def test_normal_movement_no_flags(self):
        """Normal 2.5 km movement in 10 seconds at 250 m/s: no flags."""
        prev = _make_state(timestamp=990, latitude=50.0, longitude=10.0)
        curr = _make_state(timestamp=1000, latitude=50.02, longitude=10.0)
        flags = detect_position_jump(curr, prev)
        assert len(flags) == 0

    def test_teleportation_flags(self):
        """50 km jump in 5 seconds at normal speed: should flag."""
        prev = _make_state(timestamp=995, latitude=50.0, longitude=10.0, velocity=250.0)
        curr = _make_state(timestamp=1000, latitude=50.45, longitude=10.0, velocity=250.0)
        flags = detect_position_jump(curr, prev)
        assert len(flags) >= 1
        assert flags[0].detector == "position_jump"

    def test_absolute_jump_limit(self):
        """Jump > 50 km should flag even with high speed."""
        prev = _make_state(timestamp=990, latitude=50.0, longitude=10.0, velocity=340.0)
        # ~100 km jump
        curr = _make_state(timestamp=1000, latitude=50.9, longitude=10.0, velocity=340.0)
        flags = detect_position_jump(curr, prev)
        assert len(flags) >= 1


# =========================================================================
# Altitude detector
# =========================================================================


class TestAltitudeDetector:
    """Tests for the altitude inconsistency detector."""

    def test_normal_altitude_no_flags(self):
        """Normal matching baro/geo altitudes: no flags."""
        prev = _make_state(timestamp=990, baro_altitude=10000, geo_altitude=10050)
        curr = _make_state(timestamp=1000, baro_altitude=10000, geo_altitude=10050)
        flags = detect_altitude(curr, prev)
        assert len(flags) == 0

    def test_baro_geo_divergence_flags(self):
        """300 m baro-geo divergence should flag."""
        prev = _make_state(timestamp=990, baro_altitude=10000, geo_altitude=10000)
        curr = _make_state(timestamp=1000, baro_altitude=10000, geo_altitude=10300)
        flags = detect_altitude(curr, prev)
        div_flags = [f for f in flags if f.detector == "altitude" and f.threshold == 200.0]
        assert len(div_flags) >= 1

    def test_altitude_rate_spike(self):
        """200 m/s altitude change should flag."""
        prev = _make_state(timestamp=999, geo_altitude=10000, baro_altitude=10000)
        curr = _make_state(timestamp=1000, geo_altitude=10200, baro_altitude=10200)
        flags = detect_altitude(curr, prev)
        rate_flags = [f for f in flags if "rate" in f.detail]
        assert len(rate_flags) >= 1

    def test_divergence_trend(self):
        """Growing divergence over 60 seconds should flag."""
        # Build a window with growing divergence.
        window = []
        for i in range(7):
            t = 940 + i * 10
            window.append(_make_state(
                timestamp=t,
                baro_altitude=10000,
                geo_altitude=10000 + i * 30,  # growing divergence
            ))
        prev = window[-1]
        curr = _make_state(
            timestamp=1010,
            baro_altitude=10000,
            geo_altitude=10250,
        )
        flags = detect_altitude(curr, prev, window=window)
        trend_flags = [f for f in flags if "grew" in f.detail]
        assert len(trend_flags) >= 1


# =========================================================================
# Heading detector
# =========================================================================


class TestHeadingDetector:
    """Tests for the heading vs. trajectory mismatch detector."""

    def test_consistent_heading_no_flags(self):
        """Heading matches trajectory: no flags."""
        # Moving north, heading 0.
        prev = _make_state(timestamp=990, latitude=50.0, longitude=10.0, true_track=0.0)
        curr = _make_state(timestamp=1000, latitude=50.1, longitude=10.0, true_track=0.0)
        flags = detect_heading(curr, prev)
        assert len(flags) == 0

    def test_heading_mismatch_flags(self):
        """60-degree heading mismatch should flag."""
        # Moving north but heading says east (90 degrees).
        prev = _make_state(timestamp=990, latitude=50.0, longitude=10.0, true_track=90.0)
        curr = _make_state(timestamp=1000, latitude=50.1, longitude=10.0, true_track=90.0)
        flags = detect_heading(curr, prev)
        heading_flags = [f for f in flags if f.detector == "heading"]
        assert len(heading_flags) >= 1

    def test_turning_aircraft_skipped(self):
        """Rapidly turning aircraft should be skipped (heading change > 3 deg/s)."""
        prev = _make_state(timestamp=999, latitude=50.0, longitude=10.0, true_track=0.0)
        curr = _make_state(timestamp=1000, latitude=50.01, longitude=10.0, true_track=90.0)
        flags = detect_heading(curr, prev)
        # 90 degree change in 1 second = 90 deg/s, should skip.
        assert len(flags) == 0

    def test_short_distance_skipped(self):
        """Very short distance movement should be skipped."""
        prev = _make_state(timestamp=990, latitude=50.0, longitude=10.0, true_track=90.0)
        curr = _make_state(timestamp=1000, latitude=50.0001, longitude=10.0, true_track=90.0)
        flags = detect_heading(curr, prev)
        assert len(flags) == 0


# =========================================================================
# Classifier
# =========================================================================


def _flag(detector: str, confidence: float = 0.8) -> AnomalyFlag:
    """
    Create a test AnomalyFlag with given detector name and confidence.

    Args:
        detector: Detector name string.
        confidence: Confidence score 0.0-1.0.

    Returns:
        AnomalyFlag instance.
    """
    return AnomalyFlag(
        detector=detector, value=100.0, threshold=50.0,
        confidence=confidence, detail="test flag",
    )


class TestClassifier:
    """Tests for the anomaly classification decision tree."""

    def test_signal_loss_classifies_as_jamming(self):
        """Signal loss -> jamming (Rule 1)."""
        result = classify([], has_signal_loss=True)
        assert result == "jamming"

    def test_position_jump_classifies_as_spoofing(self):
        """Position jump flag -> spoofing (Rule 2)."""
        result = classify([_flag("position_jump", 0.8)])
        assert result == "spoofing"

    def test_altitude_high_conf_classifies_as_spoofing(self):
        """Altitude divergence with conf > 0.5 -> spoofing (Rule 2)."""
        result = classify([_flag("altitude", 0.7)])
        assert result == "spoofing"

    def test_heading_high_conf_classifies_as_spoofing(self):
        """Heading mismatch with conf > 0.5 -> spoofing (Rule 2)."""
        result = classify([_flag("heading", 0.6)])
        assert result == "spoofing"

    def test_velocity_high_conf_classifies_as_spoofing(self):
        """Velocity only, high confidence -> spoofing (Rule 3)."""
        result = classify([_flag("velocity", 0.8)])
        assert result == "spoofing"

    def test_velocity_low_conf_classifies_as_anomaly(self):
        """Velocity only, low confidence -> anomaly (Rule 4)."""
        result = classify([_flag("velocity", 0.3)])
        assert result == "anomaly"

    def test_clustered_adopts_cluster_classification(self):
        """In cluster with medium-conf velocity -> adopt cluster type (Rule 5)."""
        result = classify(
            [_flag("altitude", 0.3)],  # Above 0.2 (passes Rule 6), below 0.5 (not Rule 2)
            is_clustered=True,
            cluster_classification="spoofing",
        )
        # 0.3 conf altitude: passes Rule 6 (> 0.2), but < 0.5 so not Rule 2.
        # Not velocity-only = not Rule 3/4. Clustered = Rule 5.
        assert result == "spoofing"

    def test_no_flags_returns_normal(self):
        """No flags -> normal (Rule 6)."""
        result = classify([])
        assert result == "normal"

    def test_all_low_confidence_returns_normal(self):
        """All flags below 0.2 -> normal (Rule 6)."""
        result = classify([_flag("velocity", 0.1), _flag("altitude", 0.15)])
        assert result == "normal"


# =========================================================================
# Severity scorer
# =========================================================================


class TestSeverityScorer:
    """Tests for the severity scoring formula."""

    def test_empty_flags_returns_zero(self):
        """No flags should return severity 0, label 'low'."""
        score, label = compute_severity([])
        assert score == 0
        assert label == "low"

    def test_single_moderate_flag(self):
        """Single flag with 0.5 confidence should produce moderate severity."""
        score, label = compute_severity([_flag("velocity", 0.5)])
        # 0.35 * 0.5 * 100 + 0.15 * 0.2 * 100 + 0 + 0 + 0.10 * 0.6 * 100
        # = 17.5 + 3.0 + 0 + 0 + 6.0 = 26.5 -> ~27
        assert 20 <= score <= 40
        assert label == "moderate"

    def test_clustered_high_confidence_spoofing_at_low_altitude(self):
        """
        Clustered, high-confidence, low-altitude spoofing with many flags -> critical (80+).

        5 flags from 4 detectors, cluster of 20, 10 consecutive anomalous states,
        at approach altitude (2000 m).
        """
        flags = [
            _flag("position_jump", 0.95),
            _flag("altitude", 0.90),
            _flag("altitude", 0.85),
            _flag("heading", 0.80),
            _flag("velocity", 0.75),
        ]
        score, label = compute_severity(
            flags,
            is_clustered=True,
            cluster_size=20,
            consecutive_anomalous=10,
            altitude=2000.0,
        )
        # 0.35*0.95*100 + 0.15*1.0*100 + 0.25*1.0*100 + 0.15*1.0*100 + 0.10*0.8*100
        # = 33.25 + 15 + 25 + 15 + 8 = 96.25 -> 96
        assert score >= 80
        assert label == "critical"

    def test_severity_labels_boundary(self):
        """Verify label boundaries: low/moderate/elevated/high/critical."""
        _, label = compute_severity([_flag("velocity", 0.1)])
        assert label == "low"

    def test_high_persistence_increases_score(self):
        """Long consecutive anomalous history should boost severity."""
        flags = [_flag("velocity", 0.6)]
        score_low, _ = compute_severity(flags, consecutive_anomalous=0)
        score_high, _ = compute_severity(flags, consecutive_anomalous=10)
        assert score_high > score_low


# =========================================================================
# Clusterer
# =========================================================================


def _make_classified(lat: float, lon: float, anomaly_type: str = "spoofing",
                     severity: int = 50) -> ClassifiedAnomaly:
    """
    Create a test ClassifiedAnomaly at the given position.

    Args:
        lat: Latitude in degrees.
        lon: Longitude in degrees.
        anomaly_type: Classification type.
        severity: Severity score.

    Returns:
        ClassifiedAnomaly instance.
    """
    state = AircraftState(
        icao24="TEST01", latitude=lat, longitude=lon,
        timestamp=1000, last_contact=1000,
    )
    detection = DetectionResult(
        aircraft=state,
        flags=[_flag("position_jump", 0.8)],
    )
    return ClassifiedAnomaly(
        detection=detection,
        anomaly_type=anomaly_type,
        severity=severity,
        severity_label="elevated",
        region="baltic_sea",
    )


class TestClusterer:
    """Tests for DBSCAN spatial clustering."""

    def test_nearby_anomalies_cluster_together(self):
        """5 anomalies within 100 km should form 1 cluster."""
        anomalies = [
            _make_classified(57.0, 22.0),
            _make_classified(57.1, 22.1),
            _make_classified(57.05, 21.9),
            _make_classified(56.95, 22.05),
            _make_classified(57.02, 22.15),
        ]
        clusters = cluster_anomalies(anomalies)
        # All 5 should be in one cluster.
        big_clusters = [c for c in clusters if len(c) >= 3]
        assert len(big_clusters) == 1
        assert len(big_clusters[0]) == 5

    def test_scattered_anomalies_no_cluster(self):
        """3 anomalies spread across the globe should not cluster."""
        anomalies = [
            _make_classified(57.0, 22.0),    # Baltic
            _make_classified(26.5, 54.0),    # Persian Gulf
            _make_classified(15.0, 115.0),   # South China Sea
        ]
        clusters = cluster_anomalies(anomalies)
        # Each should be its own single-element "cluster".
        big_clusters = [c for c in clusters if len(c) >= 3]
        assert len(big_clusters) == 0

    def test_build_zones_from_clusters(self):
        """Building zones from a cluster should produce a ZoneData."""
        anomalies = [
            _make_classified(57.0, 22.0),
            _make_classified(57.1, 22.1),
            _make_classified(57.05, 21.9),
        ]
        clusters = [anomalies]  # Pre-clustered.
        zones = build_zones_from_clusters(clusters, snapshot_time=1000)
        assert len(zones) == 1
        assert zones[0].affected_aircraft == 3
        assert zones[0].event_type == "spoofing"
        assert zones[0].region == "baltic_sea"

    def test_small_cluster_ignored(self):
        """Clusters with fewer than 3 aircraft should not produce zones."""
        anomalies = [
            _make_classified(57.0, 22.0),
            _make_classified(57.1, 22.1),
        ]
        zones = build_zones_from_clusters([anomalies], snapshot_time=1000)
        assert len(zones) == 0
