from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from mcp_sql.config import get_settings
from mcp_sql.core.exceptions import McpSqlBaseError
from mcp_sql.core.logger import logger

settings = get_settings()

# Initialize async engine with connection pooling
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_pre_ping=True,
    echo=False,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_read_only_session() -> AsyncGenerator[AsyncSession, Any]:
    """
    Provides an async database session strictly bound to READ ONLY mode.
    Guarantees rollback and cleanup on completion.
    """
    async with async_session_factory() as session:
        try:
            # Enforce read-only transaction state at PostgreSQL engine level
            await session.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY;"))
            yield session
        except McpSqlBaseError as exc:
            logger.error("Database session failure: %s", exc)
            await session.rollback()
            raise
        finally:
            await session.rollback()
            await session.close()


async def check_database_connection() -> bool:
    """Verifies that the database connection is alive and healthy."""
    try:
        async with get_read_only_session() as session:
            result = await session.execute(text("SELECT 1;"))
            return result.scalar() == 1
    except McpSqlBaseError as exc:
        logger.critical("Database health check error: %s", exc)
        return False


async def close_database_engine() -> None:
    """Disposes the underlying connection pool upon server shutdown."""
    logger.info("Closing database connection pool...")
    await engine.dispose()