"""
Xona Pulsar constellation signal specifications.

All values are derived from publicly available specifications and
academic publications. These drive the Pulsar Mode visualization
on the frontend, showing how Pulsar's LEO constellation would
mitigate GPS interference.

Signal strengths are in dBW (decibel-watts).

Sources:
    - GPS L1 C/A: IS-GPS-200, Table 3-Va (min received power).
    - GPS L5: IS-GPS-705, Table 3-IIb (min received power).
    - Pulsar signal level: Estimated from Xona Space Systems public
      materials and T. Reid et al., "Broadband LEO Constellations for
      Navigation," Navigation, Vol. 65, No. 2 (2018). LEO orbit
      (~1,200 km) vs GPS MEO (~20,200 km) yields ~20 dB path-loss
      advantage; combined with higher transmit power, received signal
      is approximately 22 dB above GPS L1.
    - Radius reduction factor: Conservative 6.3x derived from L5
      baseline. Jammer effective radius scales as sqrt(J/S), where
      J/S is the jammer-to-signal ratio. Higher received signal power
      reduces J/S proportionally.
"""

# GPS signal strengths (received power at ground level).
# Source: IS-GPS-200 Rev N, Table 3-Va (L1 C/A minimum received power).
GPS_L1_SIGNAL_DBW: float = -158.5

# Source: IS-GPS-705 Rev C, Table 3-IIb (L5 minimum received power).
GPS_L5_SIGNAL_DBW: float = -154.9

# Xona Pulsar signal strength (estimated).
# LEO orbit (~1,200 km) vs GPS MEO (~20,200 km) yields ~20 dB path-loss
# advantage. Combined with higher transmit power, received signal is
# approximately -136 dBW.
# Ref: T. Reid et al., "Broadband LEO Constellations for Navigation,"
# Navigation, Vol. 65, No. 2, pp. 205-220 (2018).
PULSAR_SIGNAL_DBW: float = -136.0

# Signal advantage over GPS (in dB).
# vs L1: -136 - (-158.5) = 22.5 dB ≈ 178x linear power ratio
# vs L5: -136 - (-154.9) = 18.9 dB ≈ 77.6x linear power ratio
SIGNAL_ADVANTAGE_L1_DB: float = 22.5
SIGNAL_ADVANTAGE_L5_DB: float = 18.9

# Jammer radius reduction factor.
# Jammer effective radius ∝ sqrt(J/S). Higher S reduces effective radius.
# Conservative estimate using L5 baseline: sqrt(10^(18.9/10)) ≈ 8.8,
# but Xona publishes 6.3x as their spec (accounts for practical factors).
RADIUS_REDUCTION_FACTOR: float = 6.3

# Area reduction percentage: 1 - 1/(6.3^2) = 1 - 1/39.69 = 97.48% ≈ 97.5%.
AREA_REDUCTION_PCT: float = 97.5
