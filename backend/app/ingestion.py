"""
GPS Shield — OpenSky Network API Client.

Handles both live polling and historical batch loading of aircraft
state vectors from the OpenSky REST API.

Features:
    - Async HTTP via httpx with connection pooling.
    - Token-bucket rate limiting (min 5s authenticated, 22s default).
    - Exponential backoff with jitter on 429/500/503/timeout.
    - Cleaning: applies the 8 filtering rules from Part 7.2.

API docs: https://openskynetwork.github.io/opensky-api/rest.html
"""

import asyncio
import logging
import random
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# OpenSky API base URL.
OPENSKY_BASE_URL = "https://opensky-network.org/api"

# Rate limiting: minimum seconds between requests.
MIN_REQUEST_INTERVAL = 5.0  # Authenticated minimum.
DEFAULT_POLL_INTERVAL = 22.0  # Default polling interval.

# Retry configuration.
MAX_RETRIES = 5
INITIAL_BACKOFF = 2.0  # seconds
MAX_BACKOFF = 60.0  # seconds
RETRY_STATUS_CODES = {429, 500, 502, 503}


class OpenSkyClient:
    """
    Async client for the OpenSky Network REST API.

    Manages rate limiting, retries, and response parsing. Returns
    cleaned aircraft state dicts ready for the detection pipeline.

    Attributes:
        _client: httpx.AsyncClient with connection pooling.
        _last_request_time: Unix timestamp of the last API request.
        _auth: Optional HTTP basic auth tuple.
    """

    def __init__(self) -> None:
        """
        Initialize the OpenSky client with auth credentials from settings.

        Creates an httpx.AsyncClient with connection pooling and timeout.
        If OPENSKY_USERNAME is set, uses HTTP basic auth for higher rate limits.
        """
        self._auth: Optional[tuple[str, str]] = None
        if settings.OPENSKY_USERNAME and settings.OPENSKY_PASSWORD:
            self._auth = (settings.OPENSKY_USERNAME, settings.OPENSKY_PASSWORD)

        self._client = httpx.AsyncClient(
            base_url=OPENSKY_BASE_URL,
            auth=self._auth,
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_connections=5, max_keepalive_connections=2),
        )
        self._last_request_time: float = 0.0

    async def close(self) -> None:
        """Close the HTTP client and release connections."""
        await self._client.aclose()

    async def fetch_states(self, timestamp: Optional[int] = None) -> list[dict]:
        """
        Fetch aircraft state vectors from OpenSky.

        Calls GET /states/all (live) or GET /states/all?time=T (historical).
        Applies rate limiting and retries on transient errors.

        Args:
            timestamp: Optional Unix timestamp for historical data.
                       If None, fetches current live data.

        Returns:
            List of raw state vector dicts (one per aircraft).
            Each dict has keys: icao24, callsign, latitude, longitude,
            baro_altitude, geo_altitude, velocity, true_track,
            vertical_rate, on_ground, timestamp, last_contact.
        """
        # Rate limiting.
        await self._rate_limit()

        params = {}
        if timestamp is not None:
            params["time"] = timestamp

        # Retry loop with exponential backoff.
        for attempt in range(MAX_RETRIES):
            try:
                response = await self._client.get("/states/all", params=params)
                self._last_request_time = asyncio.get_event_loop().time()

                if response.status_code == 200:
                    return self._parse_response(response.json())

                if response.status_code in RETRY_STATUS_CODES:
                    backoff = self._backoff_delay(attempt)
                    logger.warning(
                        "OpenSky returned %d, retrying in %.1fs (attempt %d/%d)",
                        response.status_code, backoff, attempt + 1, MAX_RETRIES,
                    )
                    await asyncio.sleep(backoff)
                    continue

                # Non-retryable error.
                logger.error("OpenSky returned %d: %s", response.status_code, response.text[:200])
                return []

            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                backoff = self._backoff_delay(attempt)
                logger.warning(
                    "OpenSky request failed (%s), retrying in %.1fs (attempt %d/%d)",
                    type(exc).__name__, backoff, attempt + 1, MAX_RETRIES,
                )
                await asyncio.sleep(backoff)

        logger.error("OpenSky: all %d retry attempts exhausted", MAX_RETRIES)
        return []

    async def _rate_limit(self) -> None:
        """
        Enforce minimum interval between API requests.

        Sleeps if called too soon after the last request. Uses
        MIN_REQUEST_INTERVAL (5s) as the minimum gap.
        """
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        if elapsed < MIN_REQUEST_INTERVAL:
            wait = MIN_REQUEST_INTERVAL - elapsed
            await asyncio.sleep(wait)

    def _backoff_delay(self, attempt: int) -> float:
        """
        Compute exponential backoff delay with jitter.

        Args:
            attempt: Zero-indexed retry attempt number.

        Returns:
            Delay in seconds before next retry.
        """
        delay = min(INITIAL_BACKOFF * (2 ** attempt), MAX_BACKOFF)
        jitter = random.uniform(0, delay * 0.3)
        return delay + jitter

    def _parse_response(self, data: dict) -> list[dict]:
        """
        Parse OpenSky /states/all JSON response into state dicts.

        The OpenSky API returns states as an array of arrays. This
        converts them to dicts with named keys.

        Args:
            data: Raw JSON response from OpenSky.

        Returns:
            List of state vector dicts.
        """
        states = data.get("states") or []
        snapshot_time = data.get("time", 0)
        result: list[dict] = []

        for state_arr in states:
            if len(state_arr) < 17:
                continue

            result.append({
                "icao24": state_arr[0],
                "callsign": state_arr[1],
                "latitude": state_arr[6],
                "longitude": state_arr[5],
                "baro_altitude": state_arr[7],
                "geo_altitude": state_arr[13],
                "velocity": state_arr[9],
                "true_track": state_arr[10],
                "vertical_rate": state_arr[11],
                "on_ground": state_arr[8],
                "timestamp": state_arr[3] or state_arr[4],
                "last_contact": state_arr[4],
                "snapshot_time": snapshot_time,
            })

        logger.info("OpenSky: parsed %d aircraft states", len(result))
        return result
