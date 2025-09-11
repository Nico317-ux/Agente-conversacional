from typing import Literal, Dict
from huggingface_hub import InferenceClient

class SentimentalAnalyzer:
    def __init__(self,
                 provider: str,
                 hf_token : str,
                 model_name: str):
        
        self.client = InferenceClient(provider= provider,
                                      api_key= hf_token)

        self.model_name = model_name
    
    def analyze_prompt(self, user_prompt: str) -> str:
        result = self.client.text_classification(
            user_prompt,
            model= self.model_name
        )[0]
        return f'''Supporting information to generate the response: 
        The user shows a sentiment of '{result.label}' with a confidence of {result.score}. 
        Consider this mood to subtly adapt your tone. 
        Do not mention the user's sentiment unless they explicitly ask about their mood.'''
    
