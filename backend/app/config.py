"""
GPS Shield — Application Configuration.

Loads settings from environment variables via pydantic-settings.
All configuration for the backend process lives here.

Environment variables:
    DATABASE_URL: PostgreSQL connection string (asyncpg). REQUIRED.
    OPENSKY_USERNAME: OpenSky Network username (optional).
    OPENSKY_PASSWORD: OpenSky Network password (optional).
    POLL_INTERVAL_SECONDS: Live polling interval, default 22.
    CORS_ORIGINS: Comma-separated allowed origins.
    LOG_LEVEL: Logging level, default INFO.
"""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


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
