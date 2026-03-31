"""
GPS Shield — Database Engine & Session Factory.

Creates an async SQLAlchemy engine and session maker for PostgreSQL
via asyncpg. The engine is initialized at module import and used
throughout the application lifecycle.

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
)

# Session factory — produces AsyncSession instances.
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
