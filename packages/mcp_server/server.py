"""
MCP Server for HealthSync AI
Provides tools for AI to query health data via DuckDB
"""
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from tools.health_schema import get_health_schema
from tools.health_query import execute_health_query
from tools.user_context import get_user_context

app = Server("healthsync-mcp")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="health_schema",
            description="Get schema of available health data tables (columns, types). Returns information about what health metrics are available for querying.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User ID to get schema for"
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="health_query",
            description="Execute SQL query on health data using DuckDB. Returns JSON results. Use this to answer questions about health metrics like steps, heart rate, sleep, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL query to execute on health data"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "User ID whose data to query"
                    }
                },
                "required": ["sql", "user_id"]
            }
        ),
        Tool(
            name="get_user_context",
            description="Get user preferences and context from MongoDB. Returns user profile information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User ID to get context for"
                    }
                },
                "required": ["user_id"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    try:
        if name == "health_schema":
            user_id = arguments.get("user_id", "default")
            result = await get_health_schema(user_id)
            return [TextContent(type="text", text=str(result))]
        
        elif name == "health_query":
            sql = arguments.get("sql", "")
            user_id = arguments.get("user_id", "default")
            if not sql:
                return [TextContent(type="text", text='{"error": "SQL query is required"}')]
            result = await execute_health_query(sql, user_id)
            return [TextContent(type="text", text=str(result))]
        
        elif name == "get_user_context":
            user_id = arguments.get("user_id", "default")
            result = await get_user_context(user_id)
            return [TextContent(type="text", text=str(result))]
        
        else:
            return [TextContent(type="text", text=f'{{"error": "Unknown tool: {name}"}}')]
    
    except Exception as e:
        return [TextContent(type="text", text=f'{{"error": "{str(e)}"}}')]

async def main():
    """Main entry point for MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())

