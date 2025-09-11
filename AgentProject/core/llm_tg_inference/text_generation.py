from huggingface_hub import InferenceClient
from typing import List, Dict, Optional, Generator, Union
import asyncio

class TextGenerationInference:
    def __init__(self,
                 hf_token: str,
                 model_name: str,
                 provider: str,
                 default_max_tokens: int,
                 default_temperature: float,
                 system_prompt: Optional[str] = None):
        
        #We initialized the client for inference

        self.model_name = model_name
        self.hf_token = hf_token
        self.client = InferenceClient(provider=provider, api_key=self.hf_token)
        self.default_max_tokens = default_max_tokens
        self.default_temperature = default_temperature

        #Default system prompt
        self.system_prompt = system_prompt
        
    async def generate(
            self,
            user_prompt: str,
            personality: str = None,
            sensitivity: str = None,
            conversation_history: Optional[List[Dict[str, str]]] = None,
            max_tokens: Optional[int] = None,
            temperature: Optional[float] = None,
            stream: bool = False,
            tools: Optional[List[Dict]] = None
        ) -> Union[str, Generator[str,None,None]]:
        #Generate a response from the model given a user prompt.

        messages = []
        if personality:
            self.system_prompt += f'Your personality is {personality}. You should use synonyms according to your personality. You should not indicate what your personality is to the user unless they explicitly ask for it.'
        if sensitivity:
            self.system_prompt += sensitivity
        if self.system_prompt:
            messages.append({'role': 'system', 'content': self.system_prompt})
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({'role': 'user', 'content': user_prompt})

        generation_params = {
            'model': self.model_name,
            'messages': messages,
            'max_tokens': max_tokens or self.default_max_tokens,
            'temperature': temperature or self.default_temperature,
            'stream': stream
        }

        if tools:
            generation_params['tools'] = tools
            generation_params['tool_choice'] = 'auto'

        try:
            if not stream:
                response = self.client.chat.completions.create(**generation_params)
                message = response.choices[0].message
                finish_reason = response.choices[0].finish_reason
                return message, finish_reason
            else:
                # Modo streaming
                return 'No hay metodo stream True'
        except Exception as e:
            error_msg = f'Error in generation: {str(e)}'
            if stream:
                # Para streaming, devolvemos un generador que produce el error
                def error_stream_generator():
                    yield error_msg
                return error_stream_generator()
            else:
                # Para no-streaming, devolvemos la cadena de error directamente
                return error_msg