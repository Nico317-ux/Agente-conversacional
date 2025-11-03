from typing import Optional, TypedDict, List, Dict
from langgraph.graph import StateGraph
from AgentProject.core.audio_orchestrator.stt_manager import STTManager
from AgentProject.core.humanizer.emotion_analisys import LLMEmotionAnalyzer, EmotionLabel
from AgentProject.core.humanizer.personality_manager import DinamicPersonalityManager, ConversationTopic
from AgentProject.core.llm_inference.text_generation import TextGenerationInference
from AgentProject.core.llm_inference.message_prompt import message_chat
from AgentProject.configuration.app_configuration.app_configuration import AppConfiguration
from AgentProject.core.memory.memorie_context import ConversationMemory
from AgentProject.core.audio_orchestrator.tts_manager import TTSManager
import logging
import asyncio
import threading

logging.basicConfig(
    level= logging.INFO,
    format= '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app_config = AppConfiguration()
stt_manager = STTManager(deepgram_api_key= app_config.DEEPGRAM_API_KEY)
llm_inference = TextGenerationInference(repo_id=app_config.LLM_MODEL_NAME, 
                                        hf_token= app_config.HF_TOKEN,
                                        provider= app_config.LLM_PROVIDER,
                                        default_max_tokens= app_config.LLM_MODEL_MAX_TOKENS,
                                        default_temperature= app_config.LLM_MODEL_TEMPERATURE)
emotion_enginer = LLMEmotionAnalyzer(llm_inference= llm_inference)
personality_enginer = DinamicPersonalityManager(llm_inference= llm_inference,  gender=app_config.GENDER_PERSONALITY)
conversation_memory = ConversationMemory(db_path=app_config.DB_PATH_CONTEXT_MEMORY, max_context_tokens=app_config.DEFAULT_MAX_TOKENS_MEMORIE_CONTEXT, session_id='mi_chat_1')
tts_manager = TTSManager(api_key= app_config.ELEVELABS_TOKEN, voice_id= app_config.ELEVELABS_VOICE_ID)

class StateConversacionalAgent(TypedDict):
    user_prompt: str = ''
    interim_user_prompt: str = ''
    state_transcription: bool = False
    emotion: Optional[EmotionLabel] = None
    topic: Optional[ConversationTopic] = None
    personality_prompt: str = ''
    system_prompt: str = ''
    conversation_history: List[Dict] = [{}]

def inicialize_stt(state: StateConversacionalAgent) -> StateConversacionalAgent:
    stt_manager.start_listening()
    logger.info('Grafo iniciado y escucha activa')
    return state

async def inicialize_tts(state: StateConversacionalAgent) ->StateConversacionalAgent:
    await tts_manager.start_listening()
    logger.info('TTS iniciado')
    return state

def finish_stt(state: StateConversacionalAgent) -> StateConversacionalAgent:
    stt_manager.stop_listening()
    logger.info('Escucha desactivada')
    return state

async def finish_tts(state:StateConversacionalAgent) -> StateConversacionalAgent:
    await tts_manager.stop_listening()
    logger.info('TTS cerrado')
    return state

def stt_streaming(state: StateConversacionalAgent) -> StateConversacionalAgent:
    try:
        stt_manager.start_listening()
        while True:
            try:
                result = stt_manager.get_transcription()
                if isinstance(result, tuple):
                    state['state_transcription'], sentence = result
                    if state['state_transcription']:
                        state['user_prompt'] = sentence
                        break
                    else:
                        state['interim_user_prompt'] = sentence
                else:
                    continue
            except Exception as e:
                logger.info(f'Error en la obtencion de la transcription en el agente: {str(e)}')
        return state

    except Exception as e:
        logger.error(f'Ocurrio un error en el nodo stt_streaming: {str(e)}')
        state['user_prompt'] = ''
        state['state_transcription'] = False
        state['interim_user_prompt'] = ''
        return state
    finally:
        stt_manager.clear_interruption()
        stt_manager.stop_listening()

def check_interruption(state: StateConversacionalAgent) -> str:
    if stt_manager.check_interruption():
        return 'interruption_node'
    if state['user_prompt'].lower().replace('.', '').replace(',','').strip() == 'salir':
        return 'finish_node'
    return 'continue'

async def emotion_and_topic(state: StateConversacionalAgent) -> StateConversacionalAgent:
    
    try:
        emotion_task = asyncio.create_task(emotion_enginer.analyze_emotion(state['user_prompt']))
        topic_task  =asyncio.create_task(personality_enginer.analyze_conversation_topic(state['user_prompt']))
        
        state['emotion'] = await emotion_task
        state['topic'] = await topic_task
        return state
    except Exception as e:
        logger.error(f'Error en la obtencion de topico y emociones de la conversacion: {str(e)}')
        state['emotion'] = None
        state['topic'] = None
        return state

def current_personality_blend(state: StateConversacionalAgent) -> StateConversacionalAgent:
    try:
        optimal_blend = personality_enginer.calculate_dynamic_blend(
                                                        state['emotion'],
                                                        state['topic']
                                                                )
        personality_enginer.set_personality_blend(
            optimal_blend.primary,
            optimal_blend.secondary,
            optimal_blend.primary_weight,
            optimal_blend.secondary_weight,
            optimal_blend.reasoning
        )
        return state
    except Exception as e:
        logger.error(f'Error en el establecimiento de la mezcla de personalidad: {str(e)}')
        return state
        
def personality_prompt(state: StateConversacionalAgent) -> StateConversacionalAgent:
    try:
        personality_prompt_data = personality_enginer.get_personality_prompt_data()
        state['personality_prompt'] = personality_enginer.personality_prompt_template.format(**personality_prompt_data)
        return state    
    except Exception as e:
        logger.error(f'Error en la obtencion del prompt de personalidad: {str(e)}')
        state['personality_prompt'] = ''
        return state
    
def load_dependencies_generation(state: StateConversacionalAgent) -> StateConversacionalAgent:
    try:
        state['system_prompt'] = app_config.SYSTEM_PROMPT
        state['conversation_history'] = conversation_memory.get_context()
        return state
    except Exception as e:
        logger.error(f'En la obtencion de alguna dependencias contextual {str(e)}')
        state['system_prompt'] = app_config.SYSTEM_PROMPT
        state['conversation_history'] = None
        return state

async def generation_and_tts(state: StateConversacionalAgent) -> StateConversacionalAgent:
    messages = message_chat(
        user_prompt= state['user_prompt'],
        system_prompt= state['system_prompt'],
        personality_prompt= state['personality_prompt'],
        conversation_history= state['conversation_history']
    )
    try:
        stt_manager.stop_listening()
        tts_task = asyncio.create_task(tts_manager.tts_processing(
            text_chunk=llm_inference.agenerate(messages_prompt= messages), 
            interrupt_event= stt_manager.interruption_flag))
        
        pending = {tts_task}
        while pending:
            done, pending = await asyncio.wait(
                pending,
                timeout= 0.1,
                return_when= asyncio.FIRST_COMPLETED
            )

            if stt_manager.check_interruption():
                logger.info('Interrupcion detectada en el nodo TTS')
                for task in pending:
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
                return state
        
        transcription = tts_task.result()
        await conversation_memory.add_menssage('user', state['user_prompt'])
        await conversation_memory.add_menssage('assistant', transcription)
        return state
    except Exception as e:
        logger.error(f'Error nodo TTS: {str(e)}')
        return state
    

def builder():
    builder = StateGraph(StateConversacionalAgent)
    builder.add_node('stt_node', stt_streaming)
    builder.add_node('emotion_and_topic_node', emotion_and_topic)
    builder.add_node('current_personality_blend_node', current_personality_blend)
    builder.add_node('personality_prompt_node', personality_prompt)
    builder.add_node('inicialize_stt_node', inicialize_stt)
    builder.add_node('inicialize_tts_node', inicialize_tts)
    builder.add_node('finish_stt_node',finish_stt)
    builder.add_node('finish_tts_node', finish_tts)
    builder.add_node('load_dependencies_generation_node', load_dependencies_generation)
    builder.add_node('generation_and_tts', generation_and_tts)

    builder.set_entry_point('inicialize_stt_node')
    builder.set_finish_point('finish_tts_node')

    builder.add_edge('inicialize_stt_node', 'inicialize_tts_node')
    builder.add_edge('finish_stt_node', 'finish_tts_node')
    builder.add_edge('inicialize_tts_node', 'stt_node')
    builder.add_conditional_edges(
        'stt_node',
        check_interruption, {
            'interruption_node': 'stt_node',
            'finish_node': 'finish_stt_node',
            'continue': 'emotion_and_topic_node'
        }
    )
    builder.add_conditional_edges(
        'emotion_and_topic_node',
        check_interruption,{
            'interruption_node': 'stt_node',
            'finish_node': 'finish_stt_node',
            'continue': 'current_personality_blend_node'
        }
    )
    builder.add_conditional_edges(
        'current_personality_blend_node',
        check_interruption,{
            'interruption_node': 'stt_node',
            'finish_node': 'finish_stt_node',
            'continue': 'personality_prompt_node'
        }
    )
    builder.add_conditional_edges(
        'personality_prompt_node',
        check_interruption,{
            'interruption_node': 'stt_node',
            'finish_node': 'finish_stt_node',
            'continue': 'load_dependencies_generation_node'
        }
    )
    builder.add_conditional_edges(
        'load_dependencies_generation_node',
        check_interruption,{
            'interruption_node': 'stt_node',
            'finish_node': 'finish_stt_node',
            'continue': 'generation_and_tts'
        }
    )
    builder.add_edge('generation_and_tts', 'stt_node')

    graph = builder.compile()
    return graph


graph = builder()