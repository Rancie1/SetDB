"""
Database connection and session management.

This module sets up SQLAlchemy with async support for FastAPI.
It provides a database session dependency that FastAPI routes can use.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# Create async engine
# Replace 'postgresql://' with 'postgresql+asyncpg://' for async support
# Note: We'll use psycopg (async) instead of psycopg2 for async operations
database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(
    database_url,
    echo=True,  # Log SQL queries (set to False in production)
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


async def get_db() -> AsyncSession:
    """
    Dependency function for FastAPI routes.
    
    Yields a database session and ensures it's closed after use.
    This is the recommended pattern for FastAPI dependencies.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


