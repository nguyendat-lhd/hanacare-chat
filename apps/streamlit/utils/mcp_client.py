"""
MCP Client Utility
Connect to MCP Server and call tools
"""
import asyncio
import json
import subprocess
from pathlib import Path
from mcp import ClientSession, StdioServerParameters

class MCPHealthClient:
    """Client for connecting to HealthSync MCP Server"""
    
    def __init__(self):
        self.session = None
        self.process = None
    
    async def connect(self):
        """Start MCP server and connect"""
        try:
            # Get path to MCP server (relative to project root)
            current_file = Path(__file__).resolve()
            # Navigate: utils -> streamlit -> apps -> project_root
            project_root = current_file.parent.parent.parent.parent
            server_path = project_root / "packages" / "mcp_server" / "server.py"
            
            if not server_path.exists():
                raise FileNotFoundError(f"MCP server not found at {server_path}")
            
            server_params = StdioServerParameters(
                command="python",
                args=[str(server_path)]
            )
            
            self.session = ClientSession(server_params)
            await self.session.initialize()
            return True
        except Exception as e:
            print(f"MCP connection error: {e}")
            raise
    
    async def call_tool(self, tool_name: str, arguments: dict):
        """
        Call MCP tool
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
        
        Returns:
            Tool result (dict or str)
        """
        if self.session is None:
            await self.connect()
        
        try:
            result = await self.session.call_tool(tool_name, arguments)
            
            if result.content and len(result.content) > 0:
                content_text = result.content[0].text
                # Try to parse as JSON
                try:
                    return json.loads(content_text)
                except:
                    return content_text
            else:
                return {}
        except Exception as e:
            print(f"Tool call error: {e}")
            return {"error": str(e)}
    
    async def close(self):
        """Close connection"""
        if self.session:
            try:
                await self.session.close()
            except:
                pass
            self.session = None

