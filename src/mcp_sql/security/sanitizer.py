from typing import Any

import sqlglot
from sqlglot import exp

from mcp_sql.core.exceptions import McpSqlBaseError


def enforce_query_limit(query: str, default_limit: int, max_limit: int) -> str:
    """
    Ensures the query contains a safe LIMIT clause.

    - If no LIMIT is present, injects default_limit.
    - If LIMIT exceeds max_limit, caps it to max_limit.
    """
    try:
        ast = sqlglot.parse_one(query, read="postgres")
    except McpSqlBaseError:
        # Fallback to appending LIMIT if parsing fails here (validation caught it earlier)
        return f"{query.rstrip(';')} LIMIT {default_limit};"

    limit_node = ast.find(exp.Limit)
    if limit_node and limit_node.expression:
        try:
            current_limit = int(limit_node.expression.name)
            if current_limit > max_limit:
                limit_node.expression.replace(exp.Literal.number(max_limit))
        except (ValueError, TypeError):
            limit_node.expression.replace(exp.Literal.number(default_limit))
    else:
        ast = ast.limit(default_limit)

    return ast.sql(dialect="postgres")


def mask_sensitive_data(
    rows: list[dict[str, Any]], sensitive_columns: set[str]
) -> list[dict[str, Any]]:
    """
    Redacts values of columns that match known sensitive column names (case-insensitive).
    """
    if not rows or not sensitive_columns:
        return rows

    normalized_sensitive = {col.lower() for col in sensitive_columns}
    masked_rows = []

    for row in rows:
        masked_row = {}
        for column_name, value in row.items():
            if column_name.lower() in normalized_sensitive:
                masked_row[column_name] = "[REDACTED]"
            else:
                masked_row[column_name] = value
        masked_rows.append(masked_row)

    return masked_rows
