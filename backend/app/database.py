"""
GPS Shield — Database Engine & Session Factory.

Creates an async SQLAlchemy engine and session maker for PostgreSQL
via asyncpg. Includes connection health checks and query timeouts.

Usage:
    from app.database import async_session, engine

    async with async_session() as session:
        result = await session.execute(...)
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# Async engine for PostgreSQL via asyncpg.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
    # Ping connections before use to detect stale/dropped connections.
    pool_pre_ping=True,
    # Recycle connections every 30 min to avoid idle timeout issues.
    pool_recycle=1800,
    # asyncpg connection args: 30s query timeout prevents hung queries.
    connect_args={"command_timeout": 30},
)

# Session factory — produces AsyncSession instances.
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
