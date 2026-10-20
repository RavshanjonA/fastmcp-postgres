class McpSqlBaseError(Exception):
    """Base Exception for all errors raised by this service."""



class SecurityValidationError(McpSqlBaseError):
    """Raised when an incoming query violates security or read-only rules."""



class DatabaseConnectionError(McpSqlBaseError):
    """Raised when an unable to establish or maintain connecto to PostgreSQL."""



class QueryExecutionTimeoutError(McpSqlBaseError):
    """Raised when query execution exeeds the configured timeout,"""

