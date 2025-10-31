"""
Database Configuration Module

This module handles SQLAlchemy async engine setup, session management,
and provides the Base model for all database models.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config import settings

# ============================================================================
# Database Engine Configuration
# ============================================================================

"""
Create async engine with safe options depending on the database scheme.

Notes:
- For PostgreSQL we convert the scheme to asyncpg and enable pool sizing
  options and server settings.
- For SQLite (aiosqlite) we avoid pool sizing parameters because aiosqlite
  does not support the same pooling semantics. Using pool defaults or
  NullPool avoids errors on engine creation.
"""

# Normalize URL for async drivers where appropriate
async_database_url = settings.database_url
connect_args = {}
engine_kwargs = {
    "echo": settings.database_echo,
}

if async_database_url.startswith("postgresql://"):
    # Use asyncpg dialect for PostgreSQL URLs
    async_database_url = async_database_url.replace(
        "postgresql://", "postgresql+asyncpg://"
    )
    connect_args = {
        "timeout": 10,
        "command_timeout": 10,
        "server_settings": {"application_name": settings.app_name},
    }
    engine_kwargs.update(
        {
            "pool_size": settings.database_pool_size,
            "max_overflow": settings.database_max_overflow,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        }
    )
elif async_database_url.startswith("sqlite"):
    # Keep aiosqlite URL as-is and avoid pool sizing options which are
    # incompatible with the sqlite async driver. Use NullPool semantics by
    # not specifying pool_size/max_overflow.
    # Optionally, users can set a different DB URL (postgresql) in production.
    pass
else:
    # For other DBs (e.g., explicit async URLs) try to keep defaults but
    # avoid forcing pool params unless the URL indicates PostgreSQL async.
    pass

# Attach connect_args if present
if connect_args:
    engine_kwargs["connect_args"] = connect_args

# Finally create the engine with the assembled kwargs
engine = create_async_engine(async_database_url, **engine_kwargs)

# ============================================================================
# Session Factory
# ============================================================================

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# ============================================================================
# Base Model
# ============================================================================

# Declarative base for all models
Base = declarative_base()


# ============================================================================
# Dependency Functions
# ============================================================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session.
    
    Yields an AsyncSession for use in route handlers.
    Automatically closes the session after the request is complete.
    
    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    
    Yields:
        AsyncSession: Database session for the request
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ============================================================================
# Database Initialization Functions
# ============================================================================

async def init_db() -> None:
    """
    Initialize database by creating all tables.
    
    This function should be called once at application startup
    to create all tables defined in the models.
    
    Usage:
        @app.on_event("startup")
        async def startup():
            await init_db()
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """
    Drop all tables from the database.
    
    WARNING: This will delete all data in the database.
    Only use in development/testing environments.
    
    Usage:
        @app.on_event("shutdown")
        async def shutdown():
            await drop_db()
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def close_db() -> None:
    """
    Close the database engine and dispose of all connections.
    
    This function should be called at application shutdown.
    
    Usage:
        @app.on_event("shutdown")
        async def shutdown():
            await close_db()
    """
    await engine.dispose()


# ============================================================================
# Health Check Function
# ============================================================================

async def check_db_connection() -> bool:
    """
    Check if database connection is healthy.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
            return True
    except Exception as e:
        print(f"Database connection check failed: {e}")
        return False
