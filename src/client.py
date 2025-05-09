from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
from typing import Optional, Callable, Dict, Any, List
import json
from pprint import pprint

class CustomClient:
    def __init__(self, claude_config: Dict):
        self.claude_config = claude_config
        self.list_tools = []
        self.list_server_params = []

        self._make_server_params()

    def _make_server_params(self):
        
        server_infos = self.claude_config['mcpServers']
        for arg in server_infos:
            args = server_infos[arg]
            server_params = StdioServerParameters(
                command=args['command'],
                args=args['args'], 
                env=None,  # Optional environment variables
            )
            self.list_server_params.append(server_params)


    async def _get_session(self, server_param):
        async with stdio_client(server_param) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                tools = await session.list_tools()
                return tools

    async def _get_tools(self):
        for server_param in self.list_server_params:
            tools = await self._get_session(server_param)
            json_tools = [tool.model_dump() for tool in tools.tools]
            self.list_tools.extend(json_tools)
