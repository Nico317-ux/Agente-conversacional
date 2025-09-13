from typing import Optional, List, Dict
from langchain_core.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage

def message_chat(self,
                    user_prompt: str,
                    conversation_history: List[Dict[str, str]] = None,
                    personality: Optional[str] = None,
                    sensitivity: Optional[str] = None,
                    rag_context: Optional[str] = None):

            chat_prompt_template = ChatPromptTemplate.from_messages([
                ('system', '''{system_prompt} 
                {personality_prompt} 
                {sensitivity_prompt}
                {rag_context}'''),
                MessagesPlaceholder(variable_name= 'history'),
                ('human', '{user_prompt}')
            ])

            personality_prompt = ''
            if personality:
                personality_prompt = f'''Your personality is {personality}. 
                You should use synonyms according to your personality. 
                You should not indicate what your personality is to the 
                user unless they explicitly ask for it.'''
            sensitivity_prompt = ''
            if sensitivity:
                sensitivity_prompt = sensitivity
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
                'system_prompt': self.system_prompt,
                'personality_prompt': personality_prompt,
                'sensitivity_prompt': sensitivity_prompt,
                'rag_context': rag_context_prompt,
                'history': message_history,
                'user_prompt': user_prompt
            }).to_messages()
    