import asyncio
import sys
import os
from typing import Any, Dict, List
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPBridge:
    """Bridge client to connect the AI Agent with the local MCP Server via stdio."""
    
    def __init__(self, script_path: str = "mcp_server.py"):
        self.script_path = script_path
        
        # Гарантируем использование UTF-8 для потоков ввода-вывода на Windows
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        
        self.server_params = StdioServerParameters(
            command=sys.executable,  # Используем интерпретатор из текущего venv!
            args=[self.script_path],
            env=env
        )
        self._exit_stack = None
        self.session = None

    async def connect(self):
        """Starts the MCP server subprocess and initializes the session."""
        self._exit_stack = AsyncExitStack()
        try:
            stdio_transport = await self._exit_stack.enter_async_context(stdio_client(self.server_params))
            read, write = stdio_transport
            self.session = await self._exit_stack.enter_async_context(ClientSession(read, write))
            await self.session.initialize()
        except Exception as e:
            if self._exit_stack:
                await self._exit_stack.aclose()
            raise RuntimeError(f"Failed to connect to MCP server: {e}")

    async def get_tools(self) -> List[Dict[str, Any]]:
        """Retrieves the list of tools exposed by the MCP server."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server. Call connect() first.")
        
        response = await self.session.list_tools()
        tools = []
        for tool in response.tools:
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            })
        return tools

    async def call_tool(self, name: str, arguments: dict) -> str:
        """Executes a tool on the MCP server and returns the result."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server.")
        
        try:
            result = await self.session.call_tool(name, arguments)
            if result.content:
                return "\n".join(item.text for item in result.content if hasattr(item, 'text'))
            return "Tool executed successfully but returned no text."
        except Exception as e:
            return f"Error executing tool {name}: {str(e)}"

    async def disconnect(self):
        """Gracefully shuts down the subprocess and session."""
        if self._exit_stack:
            await self._exit_stack.aclose()
            self._exit_stack = None
            self.session = None

# ---------------------------------------------------------
# Test block: Execute this file directly to test the connection
# ---------------------------------------------------------
if __name__ == "__main__":
    async def run_test():
        print("Starting MCP Bridge test...")
        bridge = MCPBridge()
        
        print("1. Connecting to MCP Server...")
        await bridge.connect()
        print("   Connected successfully!\n")
        
        print("2. Fetching available tools...")
        tools = await bridge.get_tools()
        for t in tools:
            print(f"   - {t['name']}: {t['description']}")
            
        print("\n3. Testing 'get_assignments' tool...")
        result = await bridge.call_tool("get_assignments", {"status": "Pending"})
        print(f"   Result: {result}")
        
        print("\n4. Disconnecting...")
        await bridge.disconnect()
        print("   Test completed successfully.")

    asyncio.run(run_test())