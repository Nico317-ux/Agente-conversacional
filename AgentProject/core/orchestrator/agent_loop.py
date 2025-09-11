from typing import List, Dict, Any, Optional
import json
import asyncio
import time

class AgentLoop:
    def __init__(self, text_generation, tool_dispatcher):
        self.text_generation = text_generation
        self.tool_dispatcher = tool_dispatcher
    
    async def initialize(self):
        await self.tool_dispatcher.initialize()
    
    async def close(self):
        await self.tool_dispatcher.close()

    async def run(self, 
                  user_prompt: str, 
                  personality: Dict, 
                  sensitivity: str, 
                  conversation_history: List[Dict],
                  max_iterations: int = 9) -> str:
        
        history = conversation_history or []

        try:
            available_tools = await self.tool_dispatcher.get_all_tools()
            finish_reason = None
            iteration = 0
            
            while finish_reason is None or finish_reason == 'tool_calls':
                iteration+=1
                
                response, finish_reason = await self.text_generation.generate(
                    user_prompt=user_prompt,
                    personality=personality,
                    sensitivity=sensitivity,
                    conversation_history=history,
                    tools=available_tools
                )

                print(finish_reason)
                print(response)

                if finish_reason == 'tool_calls':
                    tool_call = response.tool_calls[0]
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    server_tool = self.tool_dispatcher.get_server_for_tool(tool_name)
                    tool_result = await self.tool_dispatcher.execute_tool(server_tool,tool_name, tool_args)
                    history.append({
                        'role': 'tool',
                        'tool_call_id': tool_call.id,
                        'name': tool_name,
                        'content': json.dumps(tool_result)
                    })
                
                else:
                    return response.content
                
                if iteration == max_iterations:
                    return 'Maximo numero de bucles alcanzados'
        
        except Exception as e:
            return f'error de tipo: {str(e)}'