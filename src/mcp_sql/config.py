from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """
    Application configuration and runtime constraints.
    Loaded automatically from .env file or environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=[str(ENV_FILE), ".env"], env_file_encoding="utf-8", extra="ignore"
    )

    # Server Identification
    server_name: str = Field(
        default="secure-postgres-mcp", description="Name of MCP server instance"
    )

    # Database connectivity
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:12055@localhost:5432/bulink_view",
        description="Async PostgreSQL connections URL using asyncpg",
    )
    # Connection pool parameters
    db_pool_size: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of persistent connections maintained in the pool",
    )
    db_max_overflow: int = Field(
        default=10, ge=0, description="Number of temporary connections under peak load"
    )
    db_pool_timeout: float = Field(
        default=30.0,
        gt=0.0,
        description="Seconds to wait before failing to acquire a pool connection",
    )

    # Security limits
    max_row_limit: int = Field(
        default=100, ge=1, le=100, description="Hard upper ceiling on query result rows"
    )
    default_row_limit: int = Field(
        default=50,
        ge=1,
        description="Defult row  limit injected when missing in incoming queries",
    )
    query_timeout_seconds: float = Field(
        default=5.0, gt=0.0, description="Execution deadline for queries in seconds."
    )
    sensitive_columns: set[str] = Field(
        default={
            "password",
            "password_hash",
            "token",
            "secret",
            "api_key",
            "access_token",
            "refresh_token",
            "credit_card",
        },
        description="Column names whose values must be masked before returning to the model",
    )
    log_level: str = Field(
        default="INFO", description="Logging threshold: DEBUG, INFO, WARNING, ERROR"
    )

    @field_validator("database_url")
    @classmethod
    def validate_async_pg_url(cls, value: str) -> str:
        """Ensure the URL specifically targets the asyncpg PostgreSQL driver."""
        if not value.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DATABASE_URL must start with 'postgresql+asyncpg://'. "
                "Example: postgresql+asyncpg://user:pass@localhost:5432/dbname"
            )
        return value


@lru_cache
def get_settings() -> Settings:
    """Singleton getter for cached applications settings"""
    return Settings()
