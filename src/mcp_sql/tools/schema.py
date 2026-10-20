from typing import Any

from sqlalchemy import text

from mcp_sql.core.database import get_read_only_session
from mcp_sql.core.logger import logger


async def list_tables() -> list[str]:
    """
    Retrieves the list of accessible public tables in the PostgreSQL database.
    """
    query = text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)

    async with get_read_only_session() as session:
        result = await session.execute(query)
        tables = [row[0] for row in result.fetchall()]
        logger.info("Found %d public tables.", len(tables))
        return tables


async def describe_table(table_name: str) -> list[dict[str, Any]]:
    """
    Returns column metadata (names, types, nullability) for a given table name.

    Args:
        table_name: Name of the table to inspect.
    """
    query = text("""
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = :table_name
        ORDER BY ordinal_position;
    """)

    async with get_read_only_session() as session:
        result = await session.execute(query, {"table_name": table_name})
        columns = [
            {
                "column": row[0],
                "type": row[1],
                "nullable": row[2] == "YES",
                "default": row[3],
            }
            for row in result.fetchall()
        ]
        return columns
