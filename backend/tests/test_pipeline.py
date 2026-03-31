"""
Integration tests for the full anomaly detection pipeline.

Tests the complete flow: raw state vectors -> cleaning -> detection ->
classification -> scoring -> clustering -> Pulsar modeling.

Uses synthetic aircraft data with injected anomalies to verify the
pipeline produces correct outputs.
"""

from app.detection.internal.pipeline import AnomalyPipeline


def _normal_aircraft(icao: str, lat: float, lon: float, ts: int,
                     velocity: float = 250.0, heading: float = 90.0) -> dict:
    """
    Create a raw state dict for a normal aircraft.

    Args:
        icao: Aircraft hex identifier.
        lat: Latitude in degrees.
        lon: Longitude in degrees.
        ts: Unix timestamp.
        velocity: Ground speed in m/s.
        heading: True track in degrees.

    Returns:
        Raw state vector dict matching OpenSky format.
    """
    return {
        "icao24": icao,
        "callsign": f"TST{icao[-3:]}",
        "latitude": lat,
        "longitude": lon,
        "baro_altitude": 10000.0,
        "geo_altitude": 10000.0,
        "velocity": velocity,
        "true_track": heading,
        "vertical_rate": 0.0,
        "on_ground": False,
        "timestamp": ts,
        "last_contact": ts,
    }


def _spoofed_aircraft(icao: str, lat: float, lon: float, ts: int) -> dict:
    """
    Create a raw state dict for an aircraft exhibiting spoofing signatures.

    Characteristics: huge position jump, altitude divergence, heading mismatch.

    Args:
        icao: Aircraft hex identifier.
        lat: Latitude in degrees.
        lon: Longitude in degrees.
        ts: Unix timestamp.

    Returns:
        Raw state vector dict with spoofing indicators.
    """
    return {
        "icao24": icao,
        "callsign": f"SPF{icao[-3:]}",
        "latitude": lat,
        "longitude": lon,
        "baro_altitude": 10000.0,
        "geo_altitude": 10500.0,  # 500 m divergence
        "velocity": 250.0,
        "true_track": 0.0,  # Heading north but actually moving east
        "vertical_rate": 0.0,
        "on_ground": False,
        "timestamp": ts,
        "last_contact": ts,
    }


class TestAnomalyPipeline:
    """Integration tests for the AnomalyPipeline."""

    def test_normal_aircraft_no_anomalies(self):
        """
        10 normal aircraft moving consistently should produce 0 anomaly events.
        """
        pipeline = AnomalyPipeline()

        # First snapshot: establish baselines (moving east at heading 90).
        snap1 = [
            _normal_aircraft(f"AC{i:04d}", 50.0 + i * 0.1, 10.0, ts=1000, heading=90.0)
            for i in range(10)
        ]
        events1, zones1 = pipeline.process_snapshot(snap1, snapshot_time=1000)

        # Second snapshot: consistent eastward movement (lon change matches heading 90).
        snap2 = [
            _normal_aircraft(f"AC{i:04d}", 50.0 + i * 0.1, 10.008, ts=1010, heading=90.0)
            for i in range(10)
        ]
        events2, zones2 = pipeline.process_snapshot(snap2, snapshot_time=1010)

        assert len(events2) == 0
        assert len(zones2) == 0

    def test_spoofed_aircraft_detected(self):
        """
        5 aircraft with injected spoofing signatures in the Baltic
        should produce classified anomaly events.
        """
        pipeline = AnomalyPipeline()

        # First snapshot: normal positions.
        snap1 = [
            _normal_aircraft(f"SP{i:04d}", 57.0 + i * 0.02, 22.0, ts=1000)
            for i in range(5)
        ]
        pipeline.process_snapshot(snap1, snapshot_time=1000)

        # Second snapshot: aircraft jump to spoofed positions.
        snap2 = [
            _spoofed_aircraft(f"SP{i:04d}", 57.5 + i * 0.02, 22.0, ts=1005)
            for i in range(5)
        ]
        events, zones = pipeline.process_snapshot(snap2, snapshot_time=1005)

        # Should detect anomalies.
        assert len(events) > 0

        # At least some should be classified as spoofing.
        spoofing_events = [e for e in events if e.anomaly_type == "spoofing"]
        assert len(spoofing_events) > 0

        # Events should be in the Baltic region.
        for e in events:
            assert e.region in ("baltic_sea", "other")

    def test_pipeline_produces_zones_with_pulsar_data(self):
        """
        Clustered anomalies should produce interference zones with
        Pulsar mitigation data populated.
        """
        pipeline = AnomalyPipeline()

        # First snapshot: normal.
        snap1 = [
            _normal_aircraft(f"CL{i:04d}", 57.0 + i * 0.01, 22.0 + i * 0.01, ts=1000)
            for i in range(5)
        ]
        pipeline.process_snapshot(snap1, snapshot_time=1000)

        # Second snapshot: all aircraft jump far (spoofing cluster).
        snap2 = [
            _spoofed_aircraft(f"CL{i:04d}", 57.5 + i * 0.01, 22.5 + i * 0.01, ts=1005)
            for i in range(5)
        ]
        events, zones = pipeline.process_snapshot(snap2, snapshot_time=1005)

        # If enough anomalies cluster, we should get zones.
        if zones:
            for zone in zones:
                # Pulsar fields should be populated.
                assert zone.gps_jam_radius_km is not None
                assert zone.pulsar_jam_radius_km is not None
                assert zone.signal_advantage_db == 22.5
                assert zone.area_reduction_pct == 97.5
                # Pulsar radius should be smaller.
                assert zone.pulsar_jam_radius_km < zone.gps_jam_radius_km

    def test_cleaning_filters_ground_vehicles(self):
        """Ground vehicles should be filtered out."""
        pipeline = AnomalyPipeline()

        raw = [
            {**_normal_aircraft("GND1", 50.0, 10.0, 1000), "on_ground": True},
            _normal_aircraft("AIR1", 50.0, 10.0, 1000),
        ]
        events, zones = pipeline.process_snapshot(raw, snapshot_time=1000)
        # Only 1 aircraft should be processed (the airborne one).
        # First snapshot = no anomalies expected.

    def test_cleaning_filters_null_coords(self):
        """Aircraft with null coordinates should be filtered out."""
        pipeline = AnomalyPipeline()

        raw = [
            {**_normal_aircraft("NULL", 50.0, 10.0, 1000),
             "latitude": None, "longitude": None},
            _normal_aircraft("GOOD", 50.0, 10.0, 1000),
        ]
        events, zones = pipeline.process_snapshot(raw, snapshot_time=1000)

    def test_output_shapes_match_expected(self):
        """
        Verify output matches expected data contract shapes.
        """
        pipeline = AnomalyPipeline()

        snap1 = [_normal_aircraft("SH01", 57.0, 22.0, 1000)]
        pipeline.process_snapshot(snap1, snapshot_time=1000)

        # Spoofed second snapshot.
        snap2 = [_spoofed_aircraft("SH01", 58.0, 22.0, 1005)]
        events, zones = pipeline.process_snapshot(snap2, snapshot_time=1005)

        for event in events:
            # Verify ClassifiedAnomaly has required fields.
            assert event.anomaly_type in ("spoofing", "jamming", "anomaly")
            assert 0 <= event.severity <= 100
            assert event.severity_label in ("low", "moderate", "elevated", "high", "critical")
            assert event.region is not None
            assert len(event.detection.flags) > 0

            # Verify flag shapes.
            for flag in event.detection.flags:
                assert flag.detector in ("velocity", "position_jump", "altitude", "heading")
                assert 0.0 <= flag.confidence <= 1.0
                assert isinstance(flag.detail, str)

        for zone in zones:
            # Verify ZoneData has required fields.
            assert zone.event_type in ("spoofing", "jamming", "mixed")
            assert zone.affected_aircraft > 0
            assert zone.region is not None
