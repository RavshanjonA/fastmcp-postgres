import asyncio
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError, SQLAlchemyError

from mcp_sql.config import get_settings
from mcp_sql.core.database import get_read_only_session
from mcp_sql.core.exceptions import SecurityValidationError
from mcp_sql.core.logger import logger
from mcp_sql.security.sanitizer import enforce_query_limit, mask_sensitive_data
from mcp_sql.security.validator import validate_read_only_sql

settings = get_settings()


async def execute_read_only_query(query: str) -> dict[str, Any]:
    """
    Executes a validated read-only SQL query against the PostgreSQL database.

    Features:
    - Enforces AST-based read-only validation.
    - Caps result count with maximum row limits.
    - Masking of sensitive columns (PII / Secrets).
    - Session-level query timeout.

    Args:
        query: Raw SQL query string proposed by the LLM agent.
    """
    logger.info("Received query request: %s", query)

    # 1. AST Validation
    try:
        validate_read_only_sql(query)
    except SecurityValidationError as err:
        logger.warning("Query rejected by security validator: %s", err)
        return {"success": False, "error": str(err), "rows": []}

    # 2. Enforce Limit
    safe_query_string = enforce_query_limit(
        query=query,
        default_limit=settings.default_row_limit,
        max_limit=settings.max_row_limit,
    )

    # 3. Execution under timeout
    try:
        async with get_read_only_session() as session:
            db_coroutine = session.execute(text(safe_query_string))
            result = await asyncio.wait_for(
                db_coroutine,
                timeout=settings.query_timeout_seconds,
            )

            # Convert result rows into a list of dictionaries
            raw_columns = list(result.keys())
            rows: list[dict[str, Any]] = [
                dict(zip(raw_columns, row, strict=False)) for row in result.fetchall()
            ]

    except TimeoutError:
        logger.error("Query timed out after %s seconds", settings.query_timeout_seconds)
        return {
            "success": False,
            "error": f"Query execution timed out after {settings.query_timeout_seconds} seconds.",
            "rows": [],
        }
    except ProgrammingError as exc:
        logger.critical("SQL syntax error: %s", exc)
        return {"success": False, "error": f"SQL Syntax or Schema error {exc.orig}"}

    except OperationalError as exc:
        logger.critical("Database connectivity lost %s", exc)
        return {"success": False, "error": "Database service is temporary unavailable."}
    except SQLAlchemyError as exc:
        logger.error("Unhandled database error %s", exc)
        return {
            "success": False,
            "error": "An error occured while executing the database query.",
            "rows": [],
        }

    # 4. Redact sensitive values
    sanitized_rows = mask_sensitive_data(rows, settings.sensitive_columns)

    return {
        "success": True,
        "row_count": len(sanitized_rows),
        "columns": raw_columns,
        "rows": sanitized_rows,
    }
