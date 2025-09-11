import json
from typing import Dict, List, Optional
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio

class McpClientManager:
    def __init__(self, configuration_path: str):
        self.exit_stack = AsyncExitStack()
        self.sessions: Dict[str, ClientSession] = {}
        self.available_tools: Dict[str, List[Dict]] = {}
        self.configuration_path = configuration_path
        self.server_params: Dict[str, StdioServerParameters] = {}
    
    def load_configuration(self):
        try:
            with open(self.configuration_path, 'r') as f:
                configuration = json.load(f)
            
            mcp_servers = configuration.get('mcpServers', {})
            for server_name, server_configuration in mcp_servers.items():
                self.server_params[server_name] = StdioServerParameters(
                    command=server_configuration['command'],
                    args= server_configuration['args']
                )
        
        except Exception as e:
            print(str(e))
    
    async def initialize(self):
        self.load_configuration()

        for server_name, server_param in self.server_params.items():
            try:
                await self.connect_to_server(server_name, server_param)
                await self.discover_tools(server_name)
            except Exception as e:
                print(str(e))
        
    async def connect_to_server(self, server_name: str, server_param: StdioServerParameters):
        try:
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_param)
            )
            read_stream, write_stream = stdio_transport

            session = await self.exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )

            await session.initialize()
            self.sessions[server_name] = session
        except Exception as e:
            print(str(e))
    
    async def discover_tools(self, server_name: str):
        if server_name not in self.sessions:
            return
        
        try:
            response = await self.sessions[server_name].list_tools()
            tools = []
            for tool in response.tools:
                openai_schema = self.convert_mcp_schema_to_openai(tool.inputSchema)
                tools.append({
                'type': 'function',
                'function': {
                    'name': tool.name,
                    'description': tool.description,
                    'parameters': tool.inputSchema
                }
            })
            self.available_tools[server_name] = tools
        except Exception as e:
            print(str(e))
    
    def convert_mcp_schema_to_openai(self, mcp_schema: Dict) -> Dict:
        openai_schema = {
        'type': 'object',
        'properties': {},
        'required': []
        }
    
        if not mcp_schema or 'properties' not in mcp_schema:
            return openai_schema
        
        for prop_name, prop_schema in mcp_schema['properties'].items():
            openai_schema['properties'][prop_name] = {
                'type': prop_schema.get('type', 'string'),
                'description': prop_schema.get('description', '')
            }
        
        if 'required' in mcp_schema:
            openai_schema['required'] = mcp_schema['required']
        
        return openai_schema
    
    async def get_all_tools(self) -> List[Dict]:
        all_tools = []
        for tools in self.available_tools.values():
            all_tools.extend(tools)
        return all_tools
        
    async def execute_tool(self, server_name: str, tool_name: str, arguments: Dict) -> str:
        if server_name not in self.sessions:
            return {'success': False, 'error': f'Server {server_name} not found'}
        
        try:
            result = await self.sessions[server_name].call_tool(name=tool_name, arguments=arguments)
            return result.content[0].text
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tool': tool_name,
                'server': server_name
            }
    
    async def close(self):
        await self.exit_stack.aclose()
    
    def get_server_for_tool(self, tool_name: str) -> Optional[str]:
        for server_name, tools in self.available_tools.items():
            if any(tool['function']['name'] == tool_name for tool in tools):
                return server_name
        return None

'''async def main():
    mcp = McpClientManager(configuration_path='chatbot_console\\configuration\\mcp_configuration\\mcp_configuration.json')
    await mcp.initialize()
    print(isinstance(await mcp.execute_tool('filesystem', 'list_directory_contents', {"directory_path":"C:/Users/Nicoladis/Desktop"}), str))
    await mcp.close()

asyncio.run(main())'''