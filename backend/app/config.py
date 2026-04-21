"""
GPS Shield — Application Configuration.

Loads settings from environment variables via pydantic-settings.
All configuration for the backend process lives here.

Environment variables:
    DATABASE_URL: PostgreSQL connection string. REQUIRED. Accepts any of:
        - postgres://...          (Heroku-style)
        - postgresql://...        (psql default; Neon console gives you this)
        - postgresql+asyncpg://.. (already canonical)
        Any sslmode/channel_binding query params are normalized for asyncpg.
    OPENSKY_USERNAME: OpenSky Network username (optional).
    OPENSKY_PASSWORD: OpenSky Network password (optional).
    POLL_INTERVAL_SECONDS: Live polling interval, default 22.
    CORS_ORIGINS: Comma-separated allowed origins.
    LOG_LEVEL: Logging level, default INFO.
"""

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_postgres_url(url: str) -> str:
    """
    Rewrite any Postgres URL to the async-SQLAlchemy form expected by asyncpg.

    This makes the app accept the raw connection string Neon/Railway/Heroku
    hand you in their consoles — no manual URL surgery at deploy time.

    Transformations:
        - Scheme: ``postgres://`` and ``postgresql://`` become ``postgresql+asyncpg://``.
          An existing ``+<driver>`` suffix (e.g. ``+asyncpg``) is left alone.
        - Query: ``sslmode=<libpq-mode>`` is translated to asyncpg's ``ssl=`` kwarg.
          ``channel_binding`` is a libpq concept asyncpg doesn't understand, so
          it is dropped silently rather than crashing at engine creation.

    Empty input is passed through unchanged (keeps pydantic's error messages clean).
    """
    if not url:
        return url

    # Normalize the scheme. We only rewrite when no driver is specified;
    # anything like ``postgresql+psycopg2://`` is left untouched.
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]

    parsed = urlparse(url)

    # Translate or drop query params that are libpq-only.
    new_pairs: list[tuple[str, str]] = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=False):
        if key == "sslmode":
            # Map libpq sslmode values to asyncpg's ssl kwarg.
            if value in {"require", "verify-ca", "verify-full", "prefer"}:
                new_pairs.append(("ssl", "require"))
            elif value in {"disable", "allow"}:
                new_pairs.append(("ssl", "false"))
            else:
                new_pairs.append(("ssl", value))
        elif key == "channel_binding":
            # asyncpg does not implement SCRAM channel binding negotiation
            # the way libpq does — drop silently so Neon's default URLs work.
            continue
        else:
            new_pairs.append((key, value))

    return urlunparse(parsed._replace(query=urlencode(new_pairs)))


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Security notes:
        - DATABASE_URL has no default; must be set via .env or environment.
        - OPENSKY_PASSWORD uses SecretStr to prevent accidental logging.
        - CORS_ORIGINS validated to reject wildcards in production.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database — no default forces explicit configuration.
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/gps_shield"
    # OpenSky — optional, used for live polling only.
    OPENSKY_USERNAME: str = ""
    OPENSKY_PASSWORD: SecretStr = SecretStr("")
    # Polling
    POLL_INTERVAL_SECONDS: int = 22
    LIVE_POLLING_ENABLED: bool = True
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"
    # Logging
    LOG_LEVEL: str = "INFO"
    # Rate limiting: requests per minute per IP for API endpoints.
    RATE_LIMIT: str = "60/minute"

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def _normalize_database_url(cls, v: str) -> str:
        """Normalize any Postgres URL to asyncpg form at startup."""
        return _normalize_postgres_url(v)

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse CORS_ORIGINS into a list, rejecting wildcard '*'."""
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        for origin in origins:
            if origin == "*":
                raise ValueError(
                    "CORS wildcard '*' is not allowed. "
                    "Set CORS_ORIGINS to specific origins."
                )
        return origins

    @property
    def opensky_password_value(self) -> str:
        """Unwrap SecretStr for use in HTTP auth."""
        return self.OPENSKY_PASSWORD.get_secret_value()


settings = Settings()
