"""
Sliding window manager for aircraft state history.

Maintains a per-aircraft deque of recent states to enable temporal
analysis (velocity changes, position jumps, altitude trends). Used
by the detection pipeline to provide context for each detector.

Constants from Part 7.3:
    WINDOW_MAX_SIZE = 60 states
    WINDOW_MAX_AGE = 300 seconds (5 minutes)
    STALE_THRESHOLD = 600 seconds (cleanup after 10 minutes)
"""

from collections import deque
from typing import Optional

from app.detection.interfaces.models import AircraftState

# Window configuration from Part 7.3.
WINDOW_MAX_SIZE = 60
WINDOW_MAX_AGE = 300  # seconds
STALE_THRESHOLD = 600  # seconds


class StateWindowManager:
    """
    Manages per-aircraft sliding windows of recent state vectors.

    Each aircraft (keyed by icao24) maintains a deque of up to
    WINDOW_MAX_SIZE states, pruned to WINDOW_MAX_AGE seconds.
    Aircraft not seen for STALE_THRESHOLD seconds are removed.

    Attributes:
        _windows: Dict mapping icao24 -> deque of AircraftState.
        _anomaly_counts: Dict mapping icao24 -> consecutive anomalous state count.
    """

    def __init__(self) -> None:
        """Initialize empty window and anomaly count stores."""
        self._windows: dict[str, deque[AircraftState]] = {}
        self._anomaly_counts: dict[str, int] = {}

    def update(self, state: AircraftState) -> Optional[AircraftState]:
        """
        Add a new state to the aircraft's window and return the previous state.

        Prunes states older than WINDOW_MAX_AGE and enforces WINDOW_MAX_SIZE.
        Creates a new window if this is the first observation of this aircraft.

        Args:
            state: The new aircraft state to add.

        Returns:
            The previous state for this aircraft, or None if this is the first.
        """
        icao = state.icao24

        if icao not in self._windows:
            self._windows[icao] = deque(maxlen=WINDOW_MAX_SIZE)
            self._anomaly_counts[icao] = 0

        window = self._windows[icao]

        # Get previous state before appending.
        previous = window[-1] if window else None

        # Prune states older than WINDOW_MAX_AGE.
        cutoff = state.timestamp - WINDOW_MAX_AGE
        while window and window[0].timestamp < cutoff:
            window.popleft()

        window.append(state)
        return previous

    def get_window(self, icao24: str) -> list[AircraftState]:
        """
        Get the full state window for an aircraft.

        Args:
            icao24: Aircraft hex identifier.

        Returns:
            List of recent states (oldest first), or empty list.
        """
        if icao24 in self._windows:
            return list(self._windows[icao24])
        return []

    def increment_anomaly_count(self, icao24: str) -> int:
        """
        Increment and return the consecutive anomalous state count for an aircraft.

        Args:
            icao24: Aircraft hex identifier.

        Returns:
            Updated count of consecutive anomalous states.
        """
        self._anomaly_counts[icao24] = self._anomaly_counts.get(icao24, 0) + 1
        return self._anomaly_counts[icao24]

    def reset_anomaly_count(self, icao24: str) -> None:
        """
        Reset the consecutive anomalous state count to zero.

        Args:
            icao24: Aircraft hex identifier.
        """
        self._anomaly_counts[icao24] = 0

    def get_anomaly_count(self, icao24: str) -> int:
        """
        Get the current consecutive anomalous state count.

        Args:
            icao24: Aircraft hex identifier.

        Returns:
            Count of consecutive anomalous states.
        """
        return self._anomaly_counts.get(icao24, 0)

    def cleanup_stale(self, current_timestamp: int) -> set[str]:
        """
        Remove aircraft not seen for STALE_THRESHOLD seconds.

        Args:
            current_timestamp: The current Unix epoch timestamp.

        Returns:
            Set of icao24 identifiers that were removed (for signal loss detection).
        """
        stale_cutoff = current_timestamp - STALE_THRESHOLD
        stale_icaos: set[str] = set()

        for icao, window in list(self._windows.items()):
            if not window or window[-1].timestamp < stale_cutoff:
                stale_icaos.add(icao)
                del self._windows[icao]
                self._anomaly_counts.pop(icao, None)

        return stale_icaos

    def get_all_icao24s(self) -> set[str]:
        """
        Get all currently tracked aircraft identifiers.

        Returns:
            Set of icao24 strings.
        """
        return set(self._windows.keys())

    def get_last_position(self, icao24: str) -> Optional[AircraftState]:
        """
        Get the most recent state for an aircraft.

        Args:
            icao24: Aircraft hex identifier.

        Returns:
            The most recent AircraftState, or None if not tracked.
        """
        window = self._windows.get(icao24)
        if window:
            return window[-1]
        return None
