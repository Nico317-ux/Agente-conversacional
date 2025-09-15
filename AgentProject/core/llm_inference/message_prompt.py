from typing import Optional, List, Dict
from langchain_core.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage

def message_chat(user_prompt: str,
                system_prompt: str,
                conversation_history: List[Dict[str, str]] = None,
                personality_prompt: Optional[str] = None,
                rag_context: Optional[str] = None):

            chat_prompt_template = ChatPromptTemplate.from_messages([
                ('system', '''{system_prompt} 
                {personality_prompt} 
                {rag_context}'''),
                MessagesPlaceholder(variable_name= 'history'),
                ('human', '{user_prompt}')
            ])

            personality_prompt_message = ''
            if personality_prompt:
                personality_prompt_message = personality_prompt
            rag_context_prompt = ''
            if rag_context:
                rag_context_prompt = f'Relevant Information: {rag_context}'
            
            message_history = []
            if conversation_history:
                for msg in conversation_history:
                    role = msg.get('role', '').lower()
                    content = msg.get('content', '')
                    if role == 'user':
                        message_history.append(HumanMessage(content = content))
                    if role == 'assistant':
                        message_history.append(AIMessage(content = content))

            return chat_prompt_template.invoke({
                'system_prompt': system_prompt,
                'personality_prompt': personality_prompt_message,
                'rag_context': rag_context_prompt,
                'history': message_history,
                'user_prompt': user_prompt
            }).to_messages()
    