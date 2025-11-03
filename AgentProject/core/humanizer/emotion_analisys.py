from typing import Dict, List
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from enum import Enum

class EmotionAnalysis(BaseModel):
    primary_emotion: str = Field(description='Primary emotion, must be one of: neutral, happy, sad, angry, frustrated, excited, anxious, confused')
    secondary_emotion: str = Field(description='Secondary emotion, must be one of: neutral, happy, sad, angry, frustrated, excited, anxious, confused')
    stacks: List[str] = Field(description='List of emotional stacks or nuances')

class EmotionLabel(Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FRUSTRATED = "frustrated"
    EXCITED = "excited"
    ANXIOUS = "anxious"
    CONFUSED = "confused"

class LLMEmotionAnalyzer:
    def __init__(self, llm_inference = None):
        self.llm_inference = llm_inference
        
        self.emotion_parser = PydanticOutputParser(pydantic_object=EmotionAnalysis)
        
        self.emotion_analysis_prompt = PromptTemplate(
            template='''Analiza el estado emocional del siguiente mensaje del usuario. Responde SOLO con el formato JSON especificado.

        Emociones disponibles: neutral, happy, sad, angry, frustrated, excited, anxious, confused.

        Ejemplos:
        - 'Estoy tan feliz de verte!' → primary_emotion: 'happy', secondary_emotion: 'excited', stacks: ['joy', 'anticipation']
        - 'No sé qué hacer, todo sale mal' → primary_emotion: 'sad', secondary_emotion: 'frustrated', stacks: ['hopelessness', 'confusion']
        - 'Necesito ayuda con este problema técnico' → primary_emotion: 'neutral', secondary_emotion: 'neutral', stacks: ['curiosity']

        Formato de respuesta:
        {format_instructions}''',
            input_variables=[],
            partial_variables={'format_instructions': self.emotion_parser.get_format_instructions()}
        )

    async def analyze_emotion(self, user_prompt: str) -> Dict:

        if not self.llm_inference:
            return EmotionLabel.NEUTRAL

        try:
            prompt = self.emotion_analysis_prompt.format()
            
            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content=user_prompt)
            ]
            response  = ''
            async for chunk in self.llm_inference.agenerate(messages):
                response += chunk
            parsed = self.emotion_parser.parse(response)

            for emotion in EmotionLabel:
                if emotion.value == parsed.primary_emotion:
                    return emotion
            return EmotionLabel.NEUTRAL
            
        except Exception as e:
            print(f'Error en análisis emocional: {e}')
            return EmotionLabel.NEUTRAL