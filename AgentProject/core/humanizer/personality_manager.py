from dataclasses import dataclass
from typing import List, Dict, Optional
import yaml 
from enum import Enum
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class ConversationTopic(Enum):
    PROFESSIONAL = "professional"
    PERSONAL = "personal"
    PROBLEM_SOLVING = "problem_solving"
    EMOTIONAL_SUPPORT = "emotional_support"
    CASUAL = "casual"
    UNKNOWN = "unknown"

class TopicClassification(BaseModel):
    topic: str = Field(description='''The classified topic, must be one of: professional, personal, 
    problem_solving, emotional_support, casual''')

@dataclass
class PersonalityTraits:
    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float

@dataclass
class PersonalityBlend:
    primary: str
    secondary: str
    primary_weight: float
    secondary_weight: float
    reasoning: str

class DinamicPersonalityManager:
    def __init__(self, gender: str , config_path: str = 'AgentProject/configuration/personalities_configuration/personalities.yml',
                llm_inference = None):

        self.config = self.load_config(config_path)
        self.llm_inference = llm_inference
        self.current_blend: Optional[PersonalityBlend] = None
        self.current_gender: Optional[str] = None
        self.topic_parser = PydanticOutputParser(pydantic_object= TopicClassification)

        self.topic_classification_prompt = PromptTemplate(
            template= '''
            Clasifica el tópico principal del siguiente mensaje del usuario. Responde SOLO con el formato JSON especificado.

            Opciones de tópico: professional, personal, problem_solving, emotional_support, casual.

            Ejemplos:
            - "Necesito ayuda con mi informe de ventas" → professional
            - "Mi perro se enfermó y estoy preocupado" → personal  
            - "No puedo hacer que funcione esta aplicación" → problem_solving
            - "Me siento muy solo últimamente" → emotional_support
            - "¿Qué piensas del clima hoy?" → casual

            Formato de respuesta:
            {format_instructions}
            ''',
            input_variables= [],
            partial_variables= {'format_instructions': self.topic_parser.get_format_instructions()}
        )

        self.personality_prompt_template = PromptTemplate(
            template = '''
            Tu personalidad {primary_name} ({primary_weight}%) influenciado por {secondary_name} ({secondary_weight}%).
            Expresión de género: {gender_name}

            DESCRIPCIÓN DE PERSONALIDAD:
            {primary_description}
            Influencias de {secondary_name}: {secondary_description}

            RASGOS PSICOLÓGICOS:
            - Apertura: {openness}% (curiosidad, creatividad)
            - Responsabilidad: {conscientiousness}% (organización, confiabilidad)
            - Extraversión: {extraversion}% (sociabilidad, energía)
            - Amabilidad: {agreeableness}% (empatía, cooperación)
            - Estabilidad emocional: {emotional_stability}% (resiliencia, calma)

            ESTILO COMUNICATIVO:
            - Tono: {tone}
            - Formalidad: {formality}
            - Humor: {humor}
            - Características de género: {gender_enhancements}

            CONTEXTO ACTUAL: {reasoning}

            DIRECTRICES:
            {behavioral_guidelines}

            INCORPORA ESTA PERSONALIDAD DE MANERA NATURAL Y COHERENTE EN TODAS TUS RESPUESTAS.
            ADAPTA TU COMUNICACIÓN AL GÉNERO {gender_name_upper} SUTILMENTE.
            ''',
            input_variables= [
                "primary_name", "primary_weight", "secondary_name", "secondary_weight",
                "gender_name", "reasoning", "primary_description", "secondary_description",
                "openness", "conscientiousness", "extraversion", "agreeableness", 
                "emotional_stability", "tone", "formality", "humor", "gender_enhancements",
                "behavioral_guidelines", "gender_name_upper"
            ]
        )
        self.set_gender(gender)
        self.set_personality_blend('casual', 'formal', 70, 30, 'Initial balanced state')
    
    def load_config(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    
    def set_gender(self, gender: str) -> None:
        if gender in self.config['genders']:
            self.current_gender = gender
        else:
            self.current_gender = 'feminine'
    
    def set_personality_blend(self, primary: str, secondary: str,
                            primary_weight: float, secondary_weight: float,
                            reasoning: str = '') -> None:

        if (primary in self.config['base_personalities'] and
            secondary in self.config['base_personalities']):
            self.current_blend = PersonalityBlend(
                primary= primary,
                secondary= secondary, 
                primary_weight= primary_weight/100,
                secondary_weight= secondary_weight/100,
                reasoning= reasoning
            )

    async def analyze_conversation_topic(self, user_prompt: str) -> ConversationTopic:

        if not self.llm_inference:
            return ConversationTopic.UNKNOWN
        
        try:
            prompt = self.topic_classification_prompt.format()

            messages = [
                SystemMessage(content= prompt),
                HumanMessage(content= user_prompt)
            ]
            response, _ = self.llm_inference.generate(messages, stream = False)
            parsed = self.topic_parser.parse(response)
            for topic in ConversationTopic:
                if topic.value == parsed.topic:
                    return topic
            
            return ConversationTopic.UNKNOWN

        except Exception as e:
            print(f"Error en clasificación de tópico: {e}")
            return ConversationTopic.UNKNOWN
    
    def calculate_dynamic_blend(self, user_emotion,
                                conversation_topic: ConversationTopic) -> PersonalityBlend:
        
        emotion_rules = self.config['dynamic_blending']['sensitivity_based_rules']
        context_rules = self.config['dynamic_blending']['context_based_rules']

        emotion_rules = emotion_rules.get(user_emotion.value)
        emotion_blend = None

        if emotion_rules:
            blend_map = emotion_rules['blend']
            personalities = list(blend_map.keys())
            weights = [blend_map[p] for p in personalities]

            primary = personalities[0] if weights[0] >= weights[1] else personalities[1]
            secondary = personalities[1] if weights[0] >= weights[1] else personalities[0]
            p_weight = blend_map[primary]
            s_weight = blend_map[secondary]
            emotion_blend = (primary, secondary, p_weight, s_weight, emotion_rules['reasoning'])
        
        context_rules = context_rules.get(conversation_topic.value)
        context_blend = None

        if context_rules:
            blend_map = context_rules['blend']
            personalities = list(blend_map.keys())
            weights = [blend_map[p] for p in personalities]

            primary = personalities[0] if weights[0] >= weights[1] else personalities[1]
            secondary = personalities[1] if weights[0] >= weights[1] else personalities[0]
            p_weight = blend_map[primary]
            s_weight = blend_map[secondary]

            context_blend = (primary, secondary, p_weight, s_weight, f'Context: {conversation_topic.value}')
        
        if emotion_blend and context_blend:
            primary = emotion_blend[0]
            secondary = emotion_blend[1]
            p_weight = (emotion_blend[2] * 0.6 + context_blend[2] * 0.4)
            s_weight = (emotion_blend[3] * 0.6 + context_blend[3] * 0.4)
            reasoning = f'Emotion: {emotion_blend[4]}, Context: {context_blend[4]}'

            return PersonalityBlend(primary, secondary, p_weight, s_weight, reasoning)
        elif emotion_blend:
            return PersonalityBlend(*emotion_blend)
        elif context_blend:
            return PersonalityBlend(*context_blend)
        return self.current_blend

    def get_blended_traits(self) -> PersonalityTraits:
        if not self.current_blend:
            raise ValueError('No personality blend set')
        
        primary = self.config['base_personalities'][self.current_blend.primary]
        secondary = self.config['base_personalities'][self.current_blend.secondary]

        big_five_primary = primary['psychological_profile']['big_five']
        big_five_secondary = secondary['psychological_profile']['big_five']

        blended_traits = PersonalityTraits(
            openness= self.blend_values(big_five_primary['openness'], big_five_secondary['openness']),
            conscientiousness= self.blend_values(big_five_primary['conscientiousness'], big_five_secondary['conscientiousness']),
            agreeableness= self.blend_values(big_five_primary['agreeableness'], big_five_secondary['agreeableness']),
            extraversion= self.blend_values(big_five_primary['extraversion'], big_five_secondary['extraversion']),
            neuroticism= self.blend_values(big_five_primary['neuroticism'], big_five_secondary['neuroticism'])
        )
        return blended_traits

    def blend_values(self, primary_val: float, secondary_val: float) -> float:
        return (primary_val * self.current_blend.primary_weight +
        secondary_val * self.current_blend.secondary_weight)

    def get_personality_prompt_data(self) -> Dict:
        if not self.current_blend or not self.current_gender:
            return {}

        primary = self.config['base_personalities'][self.current_blend.primary]
        secondary = self.config['base_personalities'][self.current_blend.secondary]

        gender = self.config['genders'][self.current_gender]
        traits = self.get_blended_traits()

        primary_style = primary['communication_style']
        secondary_style = secondary['communication_style']

        tone = f'{primary_style['tone']} con matices de {secondary_style['tone']}'
        formality = f'Principalmente {primary_style['formality']} con elementos de {secondary_style['formality']}'
        humor = f'{primary_style['humor']} moderado por {secondary_style['humor']}'

        return {
            "primary_name": primary['name'],
            "primary_weight": int(self.current_blend.primary_weight * 100),
            "secondary_name": secondary['name'],
            "secondary_weight": int(self.current_blend.secondary_weight * 100),
            "gender_name": gender['name'],
            "gender_name_upper": gender['name'].upper(),
            "reasoning": self.current_blend.reasoning,
            "primary_description": primary['description'],
            "secondary_description": secondary['description'],
            "openness": int(traits.openness * 100),
            "conscientiousness": int(traits.conscientiousness * 100),
            "extraversion": int(traits.extraversion * 100),
            "agreeableness": int(traits.agreeableness * 100),
            "emotional_stability": int((1 - traits.neuroticism) * 100),
            "tone": tone,
            "formality": formality,
            "humor": humor,
            "gender_enhancements": ", ".join(gender['communication_enhancements']),
            "behavioral_guidelines": self.get_behavioral_guidelines(primary, secondary)
        }
    
    def get_behavioral_guidelines(self, primary: Dict, secondary:Dict) -> str:
        guidelines = []
        
        if 'core_motivations' in primary:
            guidelines.extend(primary['core_motivations'])
        if 'core_motivations' in secondary:
            guidelines.extend(secondary['core_motivations'][:1]) 
        
        return "\n".join([f"- {guideline}" for guideline in guidelines])