import sqlglot
from sqlglot import exp

from mcp_sql.core.exceptions import SecurityValidationError


def validate_read_only_sql(query: str) -> None:
    """
    Validates that a SQL string contains strictly one query and is safe for read-only execution.

    Uses AST parsing (sqlglot) to block:
    - Multiple statement execution (semicolon separators)
    - DDL operations (DROP, ALTER, CREATE, TRUNCATE)
    - DML modifications (INSERT, UPDATE, DELETE)
    - Administrative and transaction control statements (GRANT, REVOKE, COMMIT)
    """
    cleaned_query = query.strip()
    if not cleaned_query:
        raise SecurityValidationError("SQL query string cannot be empty.")

    try:
        expressions = sqlglot.parse(cleaned_query, read="postgres")
    except Exception as exc:
        raise SecurityValidationError(f"Invalid SQL syntax: {exc}") from exc

    # Block multiple statements (e.g., 'SELECT 1; DROP TABLE users;')
    if len(expressions) != 1:
        raise SecurityValidationError(
            f"Only a single SQL statement is allowed. Found {len(expressions)} statements."
        )

    ast = expressions[0]

    # Whitelist only read-only top-level expressions
    allowed_types = (exp.Select, exp.Union)
    if not isinstance(ast, allowed_types):
        raise SecurityValidationError(
            f"Query operation '{ast.key.upper()}' is forbidden. Only SELECT queries are permitted."
        )

    # Disallowed AST nodes anywhere inside the query tree (including subqueries and CTEs)
    forbidden_nodes = (
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Drop,
        exp.Alter,
        exp.Create,
        exp.TruncateTable,
        exp.Command,
        exp.Transaction,
        exp.Into,
    )

    for node in ast.walk():
        if isinstance(node, forbidden_nodes):
            raise SecurityValidationError(
                f"Potentially destructive operation detected: {type(node).__name__}. Query rejected."
            )
