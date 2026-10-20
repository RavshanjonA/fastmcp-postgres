import sys
from pathlib import Path

# Ensure 'src' is in sys.path so mcp_sql can be imported when running script directly
src_dir = Path(__file__).resolve().parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from fastmcp import FastMCP

from mcp_sql.config import get_settings
from mcp_sql.core.logger import logger
from mcp_sql.tools.query import execute_read_only_query
from mcp_sql.tools.schema import describe_table, list_tables

settings = get_settings()

# Initialize FastMCP Server
mcp = FastMCP(settings.server_name)


@mcp.tool()
async def get_tables() -> list[str]:
    """
    List all accessible tables in the database schema.
    Call this first to discover available database entities.
    """
    return await list_tables()


@mcp.tool()
async def inspect_table(table_name: str) -> list[dict]:
    """
    Get detailed column information (names, data types, nullability) for a table.
    Use this to understand table structure before writing SQL queries.
    """
    return await describe_table(table_name)


@mcp.tool()
async def run_sql(query: str) -> dict:
    """
    Execute a secure, read-only SELECT query against the PostgreSQL database.

    Constraints:
    - Only SELECT statements are permitted.
    - Write/modify operations (DROP, INSERT, UPDATE, DELETE) are rejected.
    - Automatic row limits and sensitive column masking are applied.
    """
    return await execute_read_only_query(query)


def main():
    """Server entrypoint."""
    logger.info("Starting %s via stdio transport...", settings.server_name)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
