"""
GPS Shield — Application Configuration.

Loads settings from environment variables via pydantic-settings.
All configuration for the backend process lives here.

Environment variables:
    DATABASE_URL: PostgreSQL connection string (asyncpg).
    OPENSKY_USERNAME: OpenSky Network username (optional).
    OPENSKY_PASSWORD: OpenSky Network password (optional).
    POLL_INTERVAL_SECONDS: Live polling interval, default 22.
    CORS_ORIGINS: Comma-separated allowed origins.
    LOG_LEVEL: Logging level, default INFO.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        DATABASE_URL: Async PostgreSQL connection string.
        OPENSKY_USERNAME: OpenSky Network API username.
        OPENSKY_PASSWORD: OpenSky Network API password.
        POLL_INTERVAL_SECONDS: Seconds between live OpenSky polls.
        CORS_ORIGINS: Comma-separated list of allowed CORS origins.
        LOG_LEVEL: Python logging level name.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/gps_shield"
    OPENSKY_USERNAME: str = ""
    OPENSKY_PASSWORD: str = ""
    POLL_INTERVAL_SECONDS: int = 22
    CORS_ORIGINS: str = "http://localhost:3000"
    LOG_LEVEL: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        """
        Parse CORS_ORIGINS string into a list of origin URLs.

        Returns:
            List of origin URL strings.
        """
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
