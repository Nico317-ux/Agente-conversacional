class PromptManager:
    @staticmethod
    def total_prompt(user_prompt: str, rag_context: str = None) -> str:
        if rag_context != None:
            if rag_context:
                return f'''Based on the following relevant information: {rag_context}, 
                    answer the user question. If the information is not sufficient, indicate that you cannot answer. The question is: {user_prompt}'''
            else:
                return f'''The user asked: {user_prompt},
                    We do not have specific documents, but respond with general knowledge: 
                    - Be honest about the limitations.
                    - Provide useful information even if it is generic, but do not offer uncertainty if that is the case.
                    - Suggest alternative resources if possible.
                    '''
        else:
            return f'The question asked by the user is: {user_prompt}'
    