"""
Anomaly classification decision tree.

Classifies a set of detector flags into one of three categories:
    - 'spoofing': GPS signal is being spoofed (false position data).
    - 'jamming': GPS signal is being denied/jammed.
    - 'anomaly': Uncertain — some flags but not enough to classify.

Implements the decision tree from Part 7.10 of the master plan.
"""

from app.detection.interfaces.models import AnomalyFlag


def classify(
    flags: list[AnomalyFlag],
    has_signal_loss: bool = False,
    is_clustered: bool = False,
    cluster_classification: str = "",
) -> str:
    """
    Classify anomaly flags into a type using the decision tree.

    Decision tree (Part 7.10):
        1. Signal loss cluster -> 'jamming'
        2. Position jump OR altitude divergence (conf > 0.5) OR divergence
           trend OR heading mismatch (conf > 0.5) AND still reporting
           -> 'spoofing'
        3. Velocity only, high confidence -> 'spoofing'
        4. Velocity only, lower confidence -> 'anomaly'
        5. In anomaly cluster -> adopt cluster classification
        6. No flags or all < 0.2 confidence -> 'normal' (discard)

    Args:
        flags: List of anomaly flags from all detectors.
        has_signal_loss: Whether the aircraft stopped reporting.
        is_clustered: Whether this detection is in a spatial cluster.
        cluster_classification: The classification of the parent cluster.

    Returns:
        Classification string: 'spoofing', 'jamming', 'anomaly', or 'normal'.
    """
    if not flags and not has_signal_loss:
        return "normal"

    # Rule 1: Signal loss -> jamming.
    if has_signal_loss:
        return "jamming"

    # Build detector-specific lookups.
    detectors_present = {f.detector for f in flags}
    max_confidence_by_detector: dict[str, float] = {}
    for f in flags:
        existing = max_confidence_by_detector.get(f.detector, 0.0)
        max_confidence_by_detector[f.detector] = max(existing, f.confidence)

    # Rule 6: All flags below 0.2 confidence -> normal.
    max_overall = max((f.confidence for f in flags), default=0.0)
    if max_overall < 0.2:
        return "normal"

    # Rule 2: Position jump, altitude, or heading with conf > 0.5 -> spoofing.
    has_position_jump = max_confidence_by_detector.get("position_jump", 0) > 0.0
    has_altitude_high = max_confidence_by_detector.get("altitude", 0) > 0.5
    has_heading_high = max_confidence_by_detector.get("heading", 0) > 0.5

    if has_position_jump or has_altitude_high or has_heading_high:
        return "spoofing"

    # Rule 3/4: Velocity only.
    if detectors_present == {"velocity"} or detectors_present <= {"velocity"}:
        if max_confidence_by_detector.get("velocity", 0) > 0.5:
            return "spoofing"
        else:
            return "anomaly"

    # Rule 5: In cluster -> adopt cluster classification.
    if is_clustered and cluster_classification:
        return cluster_classification

    # Default: something was flagged but doesn't fit neatly.
    return "anomaly"
