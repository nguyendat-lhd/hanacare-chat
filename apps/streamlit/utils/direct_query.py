"""
Direct CSV Query Utilities
Query CSV files directly using DuckDB without MCP server
"""
import duckdb
import json
import sys
from pathlib import Path
from datetime import datetime

# Add MCP tools to path for imports
project_root = Path(__file__).parent.parent.parent.parent
mcp_tools_path = project_root / "packages" / "mcp_server" / "tools"
sys.path.insert(0, str(mcp_tools_path))
sys.path.insert(0, str(project_root / "packages" / "mcp_server"))

from health_schema import get_health_schema
from health_query import execute_health_query

def get_schema_direct(user_id: str) -> dict:
    """
    Get health data schema directly (without MCP)
    
    Args:
        user_id: User ID
    
    Returns:
        Schema dictionary
    """
    import asyncio
    return asyncio.run(get_health_schema(user_id))

def execute_query_direct(sql: str, user_id: str) -> dict:
    """
    Execute SQL query directly on CSV files (without MCP)
    
    Args:
        sql: SQL query string
        user_id: User ID
    
    Returns:
        Query result dictionary
    """
    import asyncio
    return asyncio.run(execute_health_query(sql, user_id))

