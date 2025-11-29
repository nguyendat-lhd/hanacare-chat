"""
Simple MCP Client - Direct tool calls without MCP protocol
Fallback when MCP client has issues
"""
import json
import sys
from pathlib import Path
import asyncio

# Add MCP server tools to path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent
mcp_tools_path = project_root / "packages" / "mcp_server" / "tools"
sys.path.insert(0, str(mcp_tools_path))
sys.path.insert(0, str(project_root / "packages" / "mcp_server"))

from health_schema import get_health_schema
from health_query import execute_health_query
from user_context import get_user_context

class MCPHealthClientSimple:
    """Simple client that calls tools directly"""
    
    def __init__(self):
        self.connected = True
    
    async def connect(self):
        """No-op for simple client"""
        return True
    
    async def call_tool(self, tool_name: str, arguments: dict):
        """Call tool directly"""
        try:
            if tool_name == "health_schema":
                user_id = arguments.get("user_id", "default")
                result = await get_health_schema(user_id)
                return result
            elif tool_name == "health_query":
                sql = arguments.get("sql", "")
                user_id = arguments.get("user_id", "default")
                result = await execute_health_query(sql, user_id)
                return result
            elif tool_name == "get_user_context":
                user_id = arguments.get("user_id", "default")
                result = await get_user_context(user_id)
                return result
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def close(self):
        """No-op"""
        pass

