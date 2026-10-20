# Secure PostgreSQL FastMCP Service

A production-grade, read-only Model Context Protocol (MCP) server providing secure, sandboxed PostgreSQL database access for AI agents (such as Antigravity, Claude Desktop, Cursor, and Zed).

Built with **FastMCP**, **SQLAlchemy (AsyncIO)**, **SQLGlot (AST parser)**, and **Pydantic Settings**.

---

## Key Features

- **Multi-Layered Security (Defense-in-Depth):**
  - **SQL AST Validation:** Uses `sqlglot` to parse queries into an Abstract Syntax Tree. Rejects mutations (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`) and multi-statement injection (`SELECT 1; DROP TABLE users;`).
  - **Read-Only Session Enforcement:** Enforces `SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY` at the PostgreSQL connection level.
  - **PII & Secrets Redaction:** Automatically masks sensitive columns (`password`, `token`, `secret`, `api_key`, `credit_card`) with `[REDACTED]`.
  - **Automatic Limit Injection:** Caps query results to avoid context window explosion (`default: 50`, `max: 100`).
  - **Execution Timeouts:** Terminates long-running or hanging queries via `asyncio.wait_for`.
- **MCP Protocol Cleanliness:**
  - Strict STDIO hygiene: all logs are directed to `sys.stderr` to avoid corrupting MCP JSON-RPC frames over `sys.stdout`.
- **Schema Discovery for LLMs:**
  - Provides `get_tables` and `inspect_table` to eliminate hallucinated queries by allowing agents to introspect the schema before writing SQL.

---

## Architecture Overview

```text
mcp-sql-service/
├── .env.example              # Environment variables template
├── pyproject.toml            # Project dependencies and tool configurations
├── README.md                 # Documentation
│
├── tests/
│   └── test_security.py      # Injection prevention & sanitizer unit tests
│
└── src/
    └── mcp_sql/
        ├── main.py           # FastMCP entrypoint & tool declarations
        ├── config.py         # Type-safe settings via Pydantic
        │
        ├── core/
        │   ├── database.py   # Async connection pool & read-only sessions
        │   ├── exceptions.py # Domain-specific error hierarchy
        │   └── logger.py     # Stderr-only structured logging
        │
        ├── security/
        │   ├── validator.py  # AST parser for read-only validation
        │   └── sanitizer.py  # LIMIT injection and PII redaction
        │
        └── tools/
            ├── schema.py     # Table listing and metadata inspection
            └── query.py      # Safe read-only execution pipeline
```

---

## Available MCP Tools

| Tool | Parameters | Description |
| :--- | :--- | :--- |
| `get_tables` | *None* | Lists all public base tables in the PostgreSQL database. |
| `inspect_table` | `table_name: str` | Returns column names, data types, and nullability constraints. |
| `run_sql` | `query: str` | Validates, sanitizes, and executes a read-only SQL query against the database. |

---

## Installation & Setup

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended package manager)
- Running PostgreSQL database instance

### 1. Clone & Install Dependencies

```bash
git clone <repo-url>
cd mcp-sql-service

# Install dependencies using uv
uv sync
```

### 2. Configure Environment

Copy `.env.example` to `.env` and set your PostgreSQL connection details:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# PostgreSQL Async Connection String
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/your_database

# Connection Pool Settings
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30.0

# Security & Constraints
MAX_ROW_LIMIT=100
DEFAULT_ROW_LIMIT=50
QUERY_TIMEOUT_SECONDS=5.0

# Logging
LOG_LEVEL=INFO
SERVER_NAME=secure-postgres-mcp
```

### 3. Verify Database Connectivity

Test that the service can reach PostgreSQL:

```bash
uv run python -c "
import asyncio
from mcp_sql.core.database import check_database_connection

async def main():
    ok = await check_database_connection()
    print('DB Connection:', 'SUCCESS' if ok else 'FAILED')

asyncio.run(main())
"
```

---

## Running & Testing

### Running Unit Tests

Run the security and sanitizer test suite:

```bash
uv run pytest -v
```

### Manual Inspection via MCP Inspector

Inspect tools and test queries in an interactive browser UI:

```bash
npx @modelcontextprotocol/inspector uv run python src/mcp_sql/main.py
```

---

## Agent Integration

### 1. Antigravity Configuration

Add the server to `~/.gemini/config/mcp_config.json`:

```json
{
  "mcpServers": {
    "postgres-db": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/mcp-sql-service",
        "run",
        "python",
        "src/mcp_sql/main.py"
      ]
    }
  }
}
```

### 2. Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "postgres-db": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/mcp-sql-service",
        "run",
        "python",
        "src/mcp_sql/main.py"
      ]
    }
  }
}
```

### 3. Zed Editor

Add to project-level settings (`.zed/settings.json`):

```json
{
  "context_servers": {
    "postgres-db": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "src/mcp_sql/main.py"
      ]
    }
  }
}
```

---

## Security Architecture

```
[Agent Query]
      │
      ▼
┌─────────────────────────────────┐
│ 1. AST Validation (SQLGlot)     │ ──► Rejects Non-SELECT, DDL, DML, Multi-Statements
└─────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────┐
│ 2. Query Sanitizer              │ ──► Caps or injects LIMIT clause
└─────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────┐
│ 3. Read-Only Transaction Guard  │ ──► Enforces PostgreSQL READ ONLY session
└─────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────┐
│ 4. Result Redaction (PII Mask)  │ ──► Redacts passwords, API keys, tokens
└─────────────────────────────────┘
      │
      ▼
[Sanitized JSON to Agent]
```

---

## License

MIT
