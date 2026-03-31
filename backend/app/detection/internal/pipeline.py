"""
Full anomaly detection pipeline orchestrator.

Processes a snapshot of aircraft state vectors through the complete
detection pipeline:

    1. Clean raw state vectors.
    2. Update sliding windows.
    3. Run 4 aircraft-level detectors.
    4. Classify each anomaly (spoofing/jamming/anomaly).
    5. Score severity.
    6. Cluster anomalies spatially (DBSCAN).
    7. Detect signal loss events.
    8. Build interference zones.
    9. Apply Pulsar mitigation modeling.

Input: list of raw state vector dicts from OpenSky.
Output: (list of ClassifiedAnomaly events, list of ZoneData zones).
"""

from typing import Optional

from app.detection.interfaces.models import (
    AircraftState,
    ClassifiedAnomaly,
    DetectionResult,
    ZoneData,
)
from app.detection.internal.classifier import classify
from app.detection.internal.clusterer import (
    build_zones_from_clusters,
    cluster_anomalies,
    detect_signal_loss,
)
from app.detection.internal.detectors import (
    detect_altitude,
    detect_heading,
    detect_position_jump,
    detect_velocity,
)
from app.detection.internal.scorer import compute_severity
from app.detection.internal.window import StateWindowManager
from app.detection.internal.zones import classify_zone
from app.pulsar.internal.modeler import compute_pulsar_mitigation


class AnomalyPipeline:
    """
    Main anomaly detection pipeline.

    Maintains per-aircraft state windows and processes snapshots of
    aircraft state vectors through the full detection chain.

    Attributes:
        window_manager: StateWindowManager for per-aircraft history.
        _previous_icao24s: Set of icao24s from the last processed snapshot.
        _last_positions: Dict mapping icao24 -> last known AircraftState.
    """

    def __init__(self) -> None:
        """Initialize the pipeline with empty state."""
        self.window_manager = StateWindowManager()
        self._previous_icao24s: set[str] = set()
        self._last_positions: dict[str, AircraftState] = {}

    def process_snapshot(
        self, raw_states: list[dict], snapshot_time: Optional[int] = None,
    ) -> tuple[list[ClassifiedAnomaly], list[ZoneData]]:
        """
        Process a complete aircraft state snapshot through the pipeline.

        Takes raw state vector dicts from OpenSky, cleans them, runs
        all detectors, classifies, scores, clusters, and models Pulsar.

        Args:
            raw_states: List of raw state vector dicts from OpenSky API.
            snapshot_time: Unix timestamp of the snapshot (defaults to
                           max timestamp in the data).

        Returns:
            Tuple of:
                - List of ClassifiedAnomaly events (individual aircraft).
                - List of ZoneData zones (clustered interference areas
                  with Pulsar mitigation data applied).
        """
        # Step 1: Clean raw states into AircraftState models.
        states = self._clean_states(raw_states, snapshot_time)

        if not states:
            return ([], [])

        if snapshot_time is None:
            snapshot_time = max(s.timestamp for s in states)

        # Track current icao24s for signal loss detection.
        current_icao24s = {s.icao24 for s in states}

        # Steps 2-5: Per-aircraft detection, classification, scoring.
        anomalies: list[ClassifiedAnomaly] = []

        for state in states:
            # Step 2: Update window, get previous state.
            previous = self.window_manager.update(state)
            self._last_positions[state.icao24] = state

            if previous is None:
                continue  # First observation — no comparison possible.

            # Step 3: Run all 4 detectors.
            flags = []
            flags.extend(detect_velocity(state, previous))
            flags.extend(detect_position_jump(state, previous))

            window = self.window_manager.get_window(state.icao24)
            flags.extend(detect_altitude(state, previous, window=window))
            flags.extend(detect_heading(state, previous))

            if not flags:
                self.window_manager.reset_anomaly_count(state.icao24)
                continue

            # Step 4: Classify.
            consecutive = self.window_manager.increment_anomaly_count(state.icao24)
            anomaly_type = classify(flags)

            if anomaly_type == "normal":
                self.window_manager.reset_anomaly_count(state.icao24)
                continue

            # Step 5: Score severity.
            altitude = state.geo_altitude or state.baro_altitude
            severity, severity_label = compute_severity(
                flags,
                consecutive_anomalous=consecutive,
                altitude=altitude,
            )

            # Build detection result.
            detection = DetectionResult(
                aircraft=state,
                flags=flags,
                consecutive_anomalous=consecutive,
            )

            region = classify_zone(state.latitude, state.longitude)

            anomalies.append(ClassifiedAnomaly(
                detection=detection,
                anomaly_type=anomaly_type,
                severity=severity,
                severity_label=severity_label,
                region=region,
            ))

        # Step 6: Cluster anomalies spatially.
        clusters = cluster_anomalies(anomalies)

        # Mark clustered anomalies and boost confidence.
        for cluster in clusters:
            if len(cluster) >= 3:
                for anomaly in cluster:
                    anomaly.detection.is_clustered = True

        # Step 7: Detect signal loss events.
        signal_loss_zones = detect_signal_loss(
            current_icao24s=current_icao24s,
            previous_icao24s=self._previous_icao24s,
            last_positions=self._last_positions,
            snapshot_time=snapshot_time,
        )

        # Update previous icao24s for next snapshot.
        self._previous_icao24s = current_icao24s

        # Step 8: Build zones from clusters.
        zones = build_zones_from_clusters(clusters, snapshot_time)

        # Add signal loss zones.
        zones.extend(signal_loss_zones)

        # Step 9: Apply Pulsar mitigation modeling to all zones.
        zones = [compute_pulsar_mitigation(z) for z in zones]

        # Cleanup stale aircraft from windows.
        self.window_manager.cleanup_stale(snapshot_time)

        return (anomalies, zones)

    def _clean_states(
        self, raw_states: list[dict], snapshot_time: Optional[int] = None,
    ) -> list[AircraftState]:
        """
        Clean raw state vector dicts into validated AircraftState models.

        Applies the 8 filtering rules from Part 7.2:
            1. Drop on_ground == true.
            2. Drop null latitude or longitude.
            3. Drop null timestamp.
            4. Drop stale positions (> 60s behind snapshot).
            5. Drop invalid coordinates (|lat| > 90, |lon| > 180).
            6. Drop altitude > 20,000 m.
            7. Drop velocity > 400 m/s (handled by detector instead).
            8. Compute altitude discrepancy (stored in state, used by detector).

        Args:
            raw_states: List of raw state vector dicts from OpenSky API.
            snapshot_time: Unix timestamp of the snapshot for staleness check.

        Returns:
            List of cleaned AircraftState models.
        """
        cleaned: list[AircraftState] = []

        for raw in raw_states:
            # Rule 1: Drop ground vehicles.
            if raw.get("on_ground", False):
                continue

            # Rule 2: Drop null coordinates.
            lat = raw.get("latitude")
            lon = raw.get("longitude")
            if lat is None or lon is None:
                continue

            # Rule 3: Drop null timestamp.
            ts = raw.get("timestamp") or raw.get("time_position")
            if ts is None:
                continue

            # Rule 4: Drop stale positions.
            if snapshot_time and (snapshot_time - ts) > 60:
                continue

            # Rule 5: Drop invalid coordinates.
            if abs(lat) > 90 or abs(lon) > 180:
                continue

            # Rule 6: Drop extreme altitude.
            baro_alt = raw.get("baro_altitude")
            geo_alt = raw.get("geo_altitude")
            if baro_alt is not None and baro_alt > 20_000:
                continue
            if geo_alt is not None and geo_alt > 20_000:
                continue

            # Build clean state.
            state = AircraftState(
                icao24=raw.get("icao24", ""),
                callsign=(raw.get("callsign") or "").strip(),
                latitude=lat,
                longitude=lon,
                baro_altitude=baro_alt,
                geo_altitude=geo_alt,
                velocity=raw.get("velocity"),
                true_track=raw.get("true_track"),
                vertical_rate=raw.get("vertical_rate"),
                on_ground=False,
                timestamp=ts,
                last_contact=raw.get("last_contact", ts),
            )

            cleaned.append(state)

        return cleaned
