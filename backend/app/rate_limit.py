"""
GPS Shield — Rate Limiting Middleware.

IP-based rate limiting using slowapi. Returns 429 Too Many Requests
with a Retry-After header when the limit is exceeded.

Default: 60 requests/minute per IP (configurable via RATE_LIMIT env var).
Applied globally via SlowAPIMiddleware in main.py.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

# Rate limiter keyed by client IP address.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT],
)
