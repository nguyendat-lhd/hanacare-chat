"""
MCP Client Utility
Connect to MCP Server and call tools
"""
import asyncio
import json
import subprocess
from pathlib import Path

# Try to import MCP, fallback to simple client if not available
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

class MCPHealthClient:
    """Client for connecting to HealthSync MCP Server"""
    
    def __init__(self, use_simple=None):
        self.session = None
        self.read_stream = None
        self.write_stream = None
        self.server_params = None
        # If use_simple is None, auto-detect based on MCP availability
        if use_simple is None:
            self.use_simple = not MCP_AVAILABLE
        else:
            self.use_simple = use_simple or not MCP_AVAILABLE
        self._stdio_context = None  # Store the context manager
    
    async def connect(self):
        """Start MCP server and connect"""
        if self.use_simple:
            # Use simple direct tool calls
            from utils.mcp_client_simple import MCPHealthClientSimple
            self.simple_client = MCPHealthClientSimple()
            await self.simple_client.connect()
            return True
        
        try:
            # Get path to MCP server (relative to project root)
            current_file = Path(__file__).resolve()
            # Navigate: utils -> streamlit -> apps -> project_root
            project_root = current_file.parent.parent.parent.parent
            server_path = project_root / "packages" / "mcp_server" / "server.py"
            
            if not server_path.exists():
                # Try alternative path resolution
                alt_project_root = Path.cwd()
                alt_server_path = alt_project_root / "packages" / "mcp_server" / "server.py"
                if alt_server_path.exists():
                    server_path = alt_server_path
                    project_root = alt_project_root
                else:
                    raise FileNotFoundError(f"MCP server not found at {server_path} or {alt_server_path}")
            
            # Try python3 first, fallback to python
            import shutil
            python_cmd = shutil.which("python3") or shutil.which("python")
            if not python_cmd:
                raise FileNotFoundError("Python not found in PATH")
            
            self.server_params = StdioServerParameters(
                command=python_cmd,
                args=[str(server_path)]
            )
            
            # stdio_client returns a context manager, use async with
            # We need to enter the context manager and keep it alive
            try:
                self._stdio_context = stdio_client(self.server_params)
                self.read_stream, self.write_stream = await self._stdio_context.__aenter__()
                self.session = ClientSession(self.read_stream, self.write_stream)
                await self.session.initialize()
                return True
            except Exception as context_error:
                # If context manager fails, clean up and raise
                if self._stdio_context:
                    try:
                        await self._stdio_context.__aexit__(None, None, None)
                    except:
                        pass
                    self._stdio_context = None
                raise context_error
        except Exception as e:
            print(f"MCP connection error: {e}, falling back to simple client")
            # Clean up if context was entered
            if self._stdio_context:
                try:
                    await self._stdio_context.__aexit__(None, None, None)
                except:
                    pass
                self._stdio_context = None
            # Fallback to simple client
            from utils.mcp_client_simple import MCPHealthClientSimple
            self.use_simple = True
            self.simple_client = MCPHealthClientSimple()
            await self.simple_client.connect()
            return True
    
    async def call_tool(self, tool_name: str, arguments: dict):
        """
        Call MCP tool
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
        
        Returns:
            Tool result (dict or str)
        """
        if self.use_simple:
            return await self.simple_client.call_tool(tool_name, arguments)
        
        if self.session is None:
            await self.connect()
            if self.use_simple:
                return await self.simple_client.call_tool(tool_name, arguments)
        
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
            print(f"Tool call error: {e}, falling back to simple client")
            # Fallback to simple client
            if not hasattr(self, 'simple_client'):
                from utils.mcp_client_simple import MCPHealthClientSimple
                self.simple_client = MCPHealthClientSimple()
                await self.simple_client.connect()
            return await self.simple_client.call_tool(tool_name, arguments)
    
    async def close(self):
        """Close connection"""
        if self.use_simple and hasattr(self, 'simple_client'):
            await self.simple_client.close()
        elif self.session:
            try:
                await self.session.close()
            except:
                pass
            # Exit the stdio context manager
            if self._stdio_context:
                try:
                    await self._stdio_context.__aexit__(None, None, None)
                except:
                    pass
                self._stdio_context = None
            self.session = None
            self.read_stream = None
            self.write_stream = None

