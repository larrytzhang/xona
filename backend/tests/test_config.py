"""
Tests for URL normalization in app.config.

These guarantee that whatever Postgres URL a deployment target (Neon,
Railway, Heroku, Supabase) hands the operator, the app rewrites it to
the asyncpg-compatible form SQLAlchemy's async engine needs.
"""

from app.config import _normalize_postgres_url


def test_raw_neon_url_is_fully_rewritten() -> None:
    """The default URL from Neon's console must become async + asyncpg-friendly."""
    raw = (
        "postgresql://neondb_owner:pw@ep-x-pooler.c-6.us-east-1.aws.neon.tech"
        "/neondb?sslmode=require&channel_binding=require"
    )
    out = _normalize_postgres_url(raw)

    assert out.startswith("postgresql+asyncpg://"), f"scheme not rewritten: {out}"
    assert "ssl=require" in out
    assert "sslmode" not in out
    assert "channel_binding" not in out
    # Credentials, host, and path must round-trip untouched.
    assert "neondb_owner:pw@ep-x-pooler.c-6.us-east-1.aws.neon.tech/neondb" in out


def test_already_async_url_is_left_alone() -> None:
    """A canonical asyncpg URL must not be double-rewritten."""
    raw = "postgresql+asyncpg://u:p@h/db?ssl=require"
    assert _normalize_postgres_url(raw) == raw


def test_heroku_scheme_is_rewritten() -> None:
    """Heroku hands you ``postgres://`` — must map to ``postgresql+asyncpg://``."""
    raw = "postgres://u:p@h/db"
    out = _normalize_postgres_url(raw)
    assert out == "postgresql+asyncpg://u:p@h/db"


def test_non_default_driver_is_preserved() -> None:
    """An explicit driver like +psycopg2 must not be silently replaced."""
    raw = "postgresql+psycopg2://u:p@h/db"
    assert _normalize_postgres_url(raw) == raw


def test_sslmode_disable_maps_to_ssl_false() -> None:
    raw = "postgresql://u:p@h/db?sslmode=disable"
    out = _normalize_postgres_url(raw)
    assert "ssl=false" in out
    assert "sslmode" not in out


def test_empty_string_passes_through() -> None:
    """Pydantic handles empty/validation errors itself — don't interfere."""
    assert _normalize_postgres_url("") == ""


def test_unrelated_query_params_preserved() -> None:
    """Only sslmode/channel_binding are touched; everything else stays."""
    raw = "postgresql://u:p@h/db?application_name=gpsshield&pool_timeout=5"
    out = _normalize_postgres_url(raw)
    assert "application_name=gpsshield" in out
    assert "pool_timeout=5" in out
