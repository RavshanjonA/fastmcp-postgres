import pytest

from mcp_sql.core.exceptions import SecutiryValidationError
from mcp_sql.security.sanitizer import enforce_query_limit, mask_sensitive_data
from mcp_sql.security.validator import validate_read_only_sql


def test_valid_select_queries():
    """Verify that safe SELECT queries pass validation."""
    validate_read_only_sql("SELECT * FROM users;")
    validate_read_only_sql(
        "SELECT id, name FROM products WHERE price > 100 ORDER BY price DESC;"
    )
    validate_read_only_sql("SELECT count(*) FROM orders GROUP BY status;")


@pytest.mark.parametrize(
    "malicious_query",
    [
        "DROP TABLE users;",
        "DELETE FROM orders WHERE id = 1;",
        "UPDATE users SET is_admin = true;",
        "INSERT INTO users (username) VALUES ('hacker');",
        "ALTER TABLE users DROP COLUMN email;",
        "TRUNCATE TABLE logs;",
        "SELECT 1; DROP TABLE users;",  # Multi-statement injection
        "SELECT * INTO new_table FROM users;",
    ],
)
def test_block_destructive_queries(malicious_query):
    """Verify that destructive operations are caught and rejected."""
    with pytest.raises(SecutiryValidationError):
        validate_read_only_sql(malicious_query)


def test_limit_enforcement():
    """Verify automatic injection and capping of the LIMIT clause."""
    # Injects default limit
    capped = enforce_query_limit("SELECT * FROM users", default_limit=50, max_limit=100)
    assert "LIMIT 50" in capped.upper()

    # Lowers excessive limit
    capped_excess = enforce_query_limit(
        "SELECT * FROM users LIMIT 1000", default_limit=50, max_limit=100
    )
    assert "LIMIT 100" in capped_excess.upper()


def test_mask_sensitive_columns():
    """Verify sensitive columns are redacted."""
    sensitive_set = {"password", "token"}
    rows = [
        {"id": 1, "username": "alice", "password": "supersecret", "token": "xyz123"},
        {"id": 2, "username": "bob", "password": "mypassword", "token": "abc456"},
    ]
    masked = mask_sensitive_data(rows, sensitive_set)

    for row in masked:
        assert row["password"] == "[REDACTED]"
        assert row["token"] == "[REDACTED]"
        assert row["username"] in ("alice", "bob")
