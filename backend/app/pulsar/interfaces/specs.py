"""
Xona Pulsar constellation signal specifications.

All values are from Xona Space Systems' published specifications.
These drive the Pulsar Mode visualization on the frontend, showing
how Pulsar's LEO constellation would mitigate GPS interference.

Signal strengths are in dBW (decibel-watts).
"""

# GPS signal strengths (received power at ground level).
GPS_L1_SIGNAL_DBW: float = -158.5   # GPS L1 C/A signal
GPS_L5_SIGNAL_DBW: float = -154.9   # GPS L5 signal

# Xona Pulsar signal strength.
PULSAR_SIGNAL_DBW: float = -136.0   # Pulsar LEO signal

# Signal advantage over GPS (in dB).
SIGNAL_ADVANTAGE_L1_DB: float = 22.5   # vs GPS L1: -136 - (-158.5) = 22.5 dB
SIGNAL_ADVANTAGE_L5_DB: float = 18.9   # vs GPS L5: -136 - (-154.9) = 18.9 dB

# Jammer radius reduction factor (published by Xona).
# Jammer effective radius scales as sqrt(power ratio).
RADIUS_REDUCTION_FACTOR: float = 6.3   # vs L5 (conservative, Xona published spec)

# Area reduction percentage.
# Area = pi * r^2. Reduction = 1 - 1/6.3^2 = 97.48%
AREA_REDUCTION_PCT: float = 97.5       # Conservative rounded value
