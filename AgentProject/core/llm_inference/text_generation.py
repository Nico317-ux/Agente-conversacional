from langchain_core.messages.base import BaseMessage
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from typing import List, Dict, Optional, Generator, Union, AsyncGenerator
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

class TextGenerationInference:
    def __init__(self,
                 hf_token: str,
                 model_name: str,
                 provider: str,
                 default_max_tokens: int,
                 default_temperature: float,
                 system_prompt: Optional[str] = None):
    

        self.model_name = model_name
        self.hf_token = hf_token
        self.default_max_tokens = default_max_tokens
        self.default_temperature = default_temperature
        self.system_prompt = system_prompt or ''
        self.provider = provider

        self.llm = HuggingFaceEndpoint(
            repo_id= self.model_name,
            huggingfacehub_api_token= self.hf_token,
            max_new_tokens= self.default_max_tokens,
            temperature= self.default_temperature,
            streaming= True,
            provider= self.provider,
            timeout = 30
        )
        
        self.chat_model = ChatHuggingFace(llm= self.llm)

    def generate(self,
                messages_prompt: List[BaseMessage],
                tools: Optional[List[Dict]] = None,
                stream: bool = True
                ) -> Union[str, Generator[str, None, None]]:

        generation_params = {}

        if tools:
            generation_params['tools'] = tools
            generation_params['tool_choice'] = 'auto'

        try:
            if not stream:
                response = self.chat_model.invoke(messages_prompt, **generation_params)
                return response.content, response.response_metadata.get('finish_reason')
            else:
                return self.stream_generation(messages_prompt, generation_params)
        except Exception as e:
            error_msg = f'Error in generation: {str(e)}'
            if stream:
                def error_stream():
                    yield error_msg
                return error_stream()
            else:
                return error_msg, "error"

    def stream_generation(self, messages: List, generation_params: Dict) -> Generator[str, None, None]:
        try:
            chain = self.chat_model | StrOutputParser()
            for chunk in chain.stream(messages, config= {'callbacks': []}, **generation_params):
                yield chunk 

        except Exception as e:
            yield f"Error during streaming: {str(e)}"
    
    async def agenerate(self,
                        messages_prompt: List[BaseMessage],
                        tools: Optional[List[Dict]] = None) -> AsyncGenerator[str, None]:
        generation_params = {}
        if tools:
            generation_params['tools'] = tools
            generation_params['tool_choice'] = 'auto'

        try:
            chain = self.chat_model | StrOutputParser()
            async for chunk in chain.astream(messages_prompt, config={"callbacks": []}, **generation_params):
                yield chunk
            
        except Exception as e:
             yield f"Error during async streaming: {str(e)}"

    def create_langchain_runnable(self):
        prompt = ChatPromptTemplate.from_messages([
            ('system', '{system_prompt}'),
            ('human', '{human_input}')
        ])

        def format_system_prompt(input_dict):
            system_content = self.system_prompt
            if input_dict.get('personality'):
                system_content += f'Your personality is {input_dict['personality']}.'

            if input_dict.get('sensitivity'):
                system_content += f'{input_dict['sensitivity']}'
                return {'system_prompt': system_content, 'user_input': input_dict['user_input']}
            
        return (
            RunnablePassthrough.assign(
                formatted_system=format_system_prompt
            )
            | prompt
            | self.chat_model
            | StrOutputParser()
        )



