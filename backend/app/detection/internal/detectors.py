"""
Aircraft-level anomaly detectors for the GPS Shield detection pipeline.

Implements 4 individual detectors that analyze pairs of consecutive
aircraft states and produce AnomalyFlag results:

    1. Velocity detector — impossible speed / acceleration (Part 7.4)
    2. Position jump detector — teleportation (Part 7.5)
    3. Altitude detector — baro/geo divergence (Part 7.6)
    4. Heading detector — track vs. trajectory mismatch (Part 7.7)

All thresholds and confidence formulas are taken directly from
Part 7 of the master plan. Do not modify these without justification.
"""

from typing import Optional

from app.detection.interfaces.models import AircraftState, AnomalyFlag
from app.detection.internal.geo import angular_difference, compute_bearing, haversine

# ---------------------------------------------------------------------------
# Detector 1: Impossible Velocity (Part 7.4)
# ---------------------------------------------------------------------------

VELOCITY_HARD_LIMIT = 340.0       # m/s (Mach 1)
DERIVED_VELOCITY_LIMIT = 400.0    # m/s
ACCELERATION_LIMIT = 50.0         # m/s^2 (~5g)


def detect_velocity(
    current: AircraftState, previous: AircraftState
) -> list[AnomalyFlag]:
    """
    Detect impossible velocity, derived speed, or acceleration.

    Check A: Reported velocity exceeds Mach 1 (340 m/s).
    Check B: Derived velocity from consecutive positions exceeds 400 m/s.
    Check C: Acceleration exceeds 50 m/s^2 (~5g).

    Args:
        current: The current aircraft state.
        previous: The previous aircraft state.

    Returns:
        List of AnomalyFlag instances (may be empty if normal).
    """
    flags: list[AnomalyFlag] = []

    # Check A: reported velocity > hard limit
    if current.velocity is not None and current.velocity > VELOCITY_HARD_LIMIT:
        confidence = min(1.0, (current.velocity - VELOCITY_HARD_LIMIT) / (700 - VELOCITY_HARD_LIMIT))
        flags.append(AnomalyFlag(
            detector="velocity",
            value=current.velocity,
            threshold=VELOCITY_HARD_LIMIT,
            confidence=confidence,
            detail=f"Reported velocity {current.velocity:.1f} m/s exceeds Mach 1 ({VELOCITY_HARD_LIMIT} m/s)",
        ))

    # Check B: derived velocity from positions
    dt = current.timestamp - previous.timestamp
    if dt > 0:
        dist = haversine(
            previous.latitude, previous.longitude,
            current.latitude, current.longitude,
        )
        v_derived = dist / dt
        if v_derived > DERIVED_VELOCITY_LIMIT:
            confidence = min(1.0, (v_derived - DERIVED_VELOCITY_LIMIT) / 500)
            flags.append(AnomalyFlag(
                detector="velocity",
                value=v_derived,
                threshold=DERIVED_VELOCITY_LIMIT,
                confidence=confidence,
                detail=f"Derived velocity {v_derived:.1f} m/s from position change exceeds {DERIVED_VELOCITY_LIMIT} m/s",
            ))

        # Check C: impossible acceleration
        if current.velocity is not None and previous.velocity is not None:
            accel = abs(current.velocity - previous.velocity) / dt
            if accel > ACCELERATION_LIMIT:
                confidence = min(1.0, accel / 100)
                flags.append(AnomalyFlag(
                    detector="velocity",
                    value=accel,
                    threshold=ACCELERATION_LIMIT,
                    confidence=confidence,
                    detail=f"Acceleration {accel:.1f} m/s² exceeds {ACCELERATION_LIMIT} m/s² (~5g)",
                ))

    return flags


# ---------------------------------------------------------------------------
# Detector 2: Position Jump / Teleportation (Part 7.5)
# ---------------------------------------------------------------------------

POSITION_JUMP_MARGIN = 2.0       # multiplier over max possible
ABSOLUTE_JUMP_LIMIT = 50_000.0   # meters (50 km)


def detect_position_jump(
    current: AircraftState, previous: AircraftState
) -> list[AnomalyFlag]:
    """
    Detect impossible position jumps (teleportation).

    Compares actual distance traveled to the maximum possible given
    the aircraft's speed and elapsed time. Flags jumps exceeding
    2x the max possible or 50 km absolute.

    Args:
        current: The current aircraft state.
        previous: The previous aircraft state.

    Returns:
        List of AnomalyFlag instances (may be empty if normal).
    """
    flags: list[AnomalyFlag] = []

    dt = current.timestamp - previous.timestamp
    if dt <= 0:
        return flags

    actual_dist = haversine(
        previous.latitude, previous.longitude,
        current.latitude, current.longitude,
    )

    # Max possible distance based on speed.
    max_speed = max(
        current.velocity or 0,
        previous.velocity or 0,
        250.0,  # default assumption if no velocity data
    )
    max_possible = max_speed * dt * POSITION_JUMP_MARGIN

    if actual_dist > max_possible or actual_dist > ABSOLUTE_JUMP_LIMIT:
        jump_ratio = actual_dist / max_possible if max_possible > 0 else 10.0
        confidence = min(1.0, (jump_ratio - 1) / 5)
        # Ensure minimum confidence for absolute limit breaches.
        if actual_dist > ABSOLUTE_JUMP_LIMIT:
            confidence = max(confidence, 0.3)
        else:
            confidence = max(confidence, 0.0)
        flags.append(AnomalyFlag(
            detector="position_jump",
            value=actual_dist,
            threshold=max_possible,
            confidence=confidence,
            detail=f"{actual_dist / 1000:.1f} km jump in {dt} seconds "
                   f"(max possible: {max_possible / 1000:.1f} km)",
        ))

    return flags


# ---------------------------------------------------------------------------
# Detector 3: Altitude Inconsistency (Part 7.6)
# ---------------------------------------------------------------------------

ALTITUDE_DIVERGENCE_WARN = 200.0      # meters
ALTITUDE_RATE_LIMIT = 100.0           # m/s


def detect_altitude(
    current: AircraftState,
    previous: AircraftState,
    window: Optional[list[AircraftState]] = None,
) -> list[AnomalyFlag]:
    """
    Detect altitude inconsistencies: baro/geo divergence, rate spikes, trends.

    Check A: |baro_altitude - geo_altitude| exceeds 200 m warning threshold.
    Check B: Altitude rate of change exceeds 100 m/s.
    Check C: Growing baro-geo divergence trend over 30+ seconds.

    Args:
        current: The current aircraft state.
        previous: The previous aircraft state.
        window: Optional list of recent states for trend analysis.

    Returns:
        List of AnomalyFlag instances (may be empty if normal).
    """
    flags: list[AnomalyFlag] = []

    # Check A: baro vs geo altitude divergence
    if current.baro_altitude is not None and current.geo_altitude is not None:
        divergence = abs(current.baro_altitude - current.geo_altitude)
        if divergence > ALTITUDE_DIVERGENCE_WARN:
            confidence = min(1.0, (divergence - ALTITUDE_DIVERGENCE_WARN) / 300)
            flags.append(AnomalyFlag(
                detector="altitude",
                value=divergence,
                threshold=ALTITUDE_DIVERGENCE_WARN,
                confidence=confidence,
                detail=f"Baro-geo altitude divergence {divergence:.0f} m "
                       f"(warn: {ALTITUDE_DIVERGENCE_WARN} m)",
            ))

    # Check B: altitude rate of change
    dt = current.timestamp - previous.timestamp
    if dt > 0:
        # Use geo_altitude preferentially, fall back to baro.
        alt_curr = current.geo_altitude if current.geo_altitude is not None else current.baro_altitude
        alt_prev = previous.geo_altitude if previous.geo_altitude is not None else previous.baro_altitude
        if alt_curr is not None and alt_prev is not None:
            rate = abs(alt_curr - alt_prev) / dt
            if rate > ALTITUDE_RATE_LIMIT:
                confidence = min(1.0, rate / 200)
                flags.append(AnomalyFlag(
                    detector="altitude",
                    value=rate,
                    threshold=ALTITUDE_RATE_LIMIT,
                    confidence=confidence,
                    detail=f"Altitude rate {rate:.1f} m/s exceeds {ALTITUDE_RATE_LIMIT} m/s",
                ))

    # Check C: growing divergence trend over window
    if window and len(window) >= 3:
        _check_divergence_trend(window, current, flags)

    return flags


def _check_divergence_trend(
    window: list[AircraftState],
    current: AircraftState,
    flags: list[AnomalyFlag],
) -> None:
    """
    Check for a growing baro-geo altitude divergence trend.

    Requires at least 30 seconds of window data. If the divergence
    has grown by more than 150 m across the window, flag it.

    Args:
        window: Recent aircraft states (oldest first).
        current: The current state.
        flags: List to append any new flags to (modified in place).
    """
    # Compute divergences for states that have both altitudes.
    divergences = []
    for state in window:
        if state.baro_altitude is not None and state.geo_altitude is not None:
            divergences.append((state.timestamp, abs(state.baro_altitude - state.geo_altitude)))

    if current.baro_altitude is not None and current.geo_altitude is not None:
        divergences.append((current.timestamp, abs(current.baro_altitude - current.geo_altitude)))

    if len(divergences) < 2:
        return

    # Check time span (need at least 30 seconds).
    time_span = divergences[-1][0] - divergences[0][0]
    if time_span < 30:
        return

    div_change = divergences[-1][1] - divergences[0][1]
    if div_change > 150:
        confidence = min(1.0, div_change / 500)
        flags.append(AnomalyFlag(
            detector="altitude",
            value=div_change,
            threshold=150.0,
            confidence=confidence,
            detail=f"Baro-geo divergence grew {div_change:.0f} m over {time_span:.0f} seconds",
        ))


# ---------------------------------------------------------------------------
# Detector 4: Heading vs. Trajectory Mismatch (Part 7.7)
# ---------------------------------------------------------------------------

HEADING_WARN = 30.0        # degrees
HEADING_MIN_DISTANCE = 500.0  # meters (need enough for reliable bearing)


def detect_heading(
    current: AircraftState, previous: AircraftState
) -> list[AnomalyFlag]:
    """
    Detect mismatch between reported heading and derived trajectory bearing.

    Computes the bearing from previous to current position and compares
    it to the reported true_track heading. Skips if the aircraft is
    turning (heading change > 3 deg/s) or distance is too short.

    Args:
        current: The current aircraft state.
        previous: The previous aircraft state.

    Returns:
        List of AnomalyFlag instances (may be empty if normal).
    """
    flags: list[AnomalyFlag] = []

    # Need reported heading on at least the current state.
    if current.true_track is None:
        return flags

    dt = current.timestamp - previous.timestamp
    if dt <= 0:
        return flags

    # Check if aircraft is turning (skip if so).
    if previous.true_track is not None:
        heading_change_rate = angular_difference(current.true_track, previous.true_track) / dt
        if heading_change_rate > 3.0:
            return flags  # Aircraft is maneuvering, skip.

    # Need enough distance for a reliable bearing estimate.
    dist = haversine(
        previous.latitude, previous.longitude,
        current.latitude, current.longitude,
    )
    if dist < HEADING_MIN_DISTANCE:
        return flags

    # Compute derived bearing from positions.
    derived_bearing = compute_bearing(
        previous.latitude, previous.longitude,
        current.latitude, current.longitude,
    )

    mismatch = angular_difference(current.true_track, derived_bearing)

    if mismatch > HEADING_WARN:
        confidence = min(1.0, (mismatch - HEADING_WARN) / 60)
        flags.append(AnomalyFlag(
            detector="heading",
            value=mismatch,
            threshold=HEADING_WARN,
            confidence=confidence,
            detail=f"Heading mismatch {mismatch:.1f}° "
                   f"(reported: {current.true_track:.1f}°, derived: {derived_bearing:.1f}°)",
        ))

    return flags
