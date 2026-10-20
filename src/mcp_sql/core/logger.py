import logging
import sys

from mcp_sql.config import get_settings


def setup_logger(name: str = "mcp_sql") -> logging.Logger:
    """
    Configures a logger explicitly routed to sys.stderr.
    
    CRITICAL: In stdio transport mode, sys.stdout is reserved exclusively 
    for MCP JSON-RPC frames. Any arbitrary print to stdout breaks communication.
    """
    settings = get_settings()
    app_logger = logging.getLogger(name)

    if not app_logger.handlers:
        app_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
        
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        app_logger.addHandler(handler)

    return app_logger


logger = setup_logger()