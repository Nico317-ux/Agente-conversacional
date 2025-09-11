from core.llm_tg_inference.text_generation import TextGenerationInference
from core.memory.memorie_context import ConversationMemory
from core.rag.rag import RAGProcessor
from core.humanizer.personality import PersonalityManager
from core.humanizer.sentiment import SentimentalAnalyzer
from core.orchestrator.router import Router
from core.orchestrator.prompt_manager import PromptManager
from core.audio_orchestrator.stt import SpeechToText
from core.audio_orchestrator.tts import TextToSpeech
from core.apparence import apparence_console
from core.orchestrator.agent_loop import AgentLoop
from mcp_client.client_manager import McpClientManager
import time
import asyncio
from configuration.app_configuration.app_configuration import AppConfiguration

config = AppConfiguration()
router = Router()
prompt_manager = PromptManager()
personality = PersonalityManager(default_personality='friendly')
audio_recoder = SpeechToText(provider= config.STT_MODEL_PROVIDER, hf_token= config.HF_TOKEN)
text_to_speech = TextToSpeech(api_key=config.ELEVELABS_TOKEN, voice_id=config.ELEVELABS_VOICE_ID)
sensitivity = SentimentalAnalyzer(hf_token= config.HF_TOKEN, model_name= config.SENTIMENTAL_MODEL_NAME, provider= config.EMBEDDING_PROVIDER)
tg_inference = TextGenerationInference(hf_token=config.HF_TOKEN, model_name=config.LLM_MODEL_NAME, provider=config.LLM_PROVIDER, system_prompt=config.SYSTEM_PROMPT, 
                            default_max_tokens=config.LLM_MODEL_MAX_TOKENS, default_temperature=config.LLM_MODEL_TEMPERATURE)
memory = ConversationMemory(db_path=config.DB_PATH_CONTEXT_MEMORY, session_id='mi_chat_1', max_context_tokens=config.DEFAULT_MAX_TOKENS_MEMORIE_CONTEXT)
rag_processor = RAGProcessor(hf_token=config.HF_TOKEN, provider=config.EMBEDDING_PROVIDER, score_threshold=config.RAG_SCORE_THRESHOLD, 
                             top_k=config.RAG_TOP_K, vector_db_path=config.DB_PATH_VECTO_RAG, db_path_cache= config.DB_PATH_EMBEDDING_CACHE, name_model= config.EMBEDDING_MODEL_NAME)
client_manager = McpClientManager(configuration_path= config.MCP_CONFIGURATION_JSON_PATH)

agent_loop = AgentLoop(text_generation=tg_inference, tool_dispatcher= client_manager)

async def chat_cli():
    apparence_console.display_banner()
    await agent_loop.initialize()
    await apparence_console.initialize_all_components()
    modality = str(input('Por favor una modalidad de comunicación para esta sección (Texto o Audio): '))
    while True:
        try:
            if modality.lower() == 'audio':
                try:
                    try:
                        input('Presione enter para empezar a grabar')
                    except KeyboardInterrupt:
                        pass
                    finally:
                        audio_recoder.start()
                        input('🔊 Grabando... Presiona Enter para detener')
                except KeyboardInterrupt:
                    pass
                finally: 
                    user_input = audio_recoder.stop().replace('.', ' ').strip()
                    print(f'Tu: {user_input}')
            if modality.lower() == 'texto':
                user_input = str(input('Tu: '))
            if user_input.lower() == 'salir':
                break
            context = memory.get_context()
            #user_sensitivity = sensitivity.analyze_prompt(user_prompt= user_input)
            '''requires_rag = router.router(user_input)
            if not requires_rag:
                augmented_prompt = prompt_manager.total_prompt(user_prompt = user_input)
            else:
                # 1. Retrieve relevant content
                relevant_chunks = rag_processor.retrieve_relevant_chucks(query=user_input)
                rag_context = rag_processor.format_context(relevant_chunks) if relevant_chunks else '' 
                augmented_prompt = prompt_manager.total_prompt(user_prompt= user_input, rag_context= rag_context)'''
            # Combine RAG context with user prompt
            print('Bot: ', end='', flush=True)
            # We use streaming=True
            response = await agent_loop.run(
                                    user_prompt = user_input,
                                    conversation_history = context,
                                    personality = personality.current,
                                    sensitivity = None
                                                )
            
            if len(response) <= 0:
                text_to_speech.text_reproduction(text= response)
                memory.add_message('user', user_input)
                memory.add_message('assistant', response)
                print('Respondido por audio', end='' ,flush=True)
            else:
                for chunk in response:
                    print(chunk, end='', flush=True)
                    time.sleep(0.03)
                memory.add_message('user', user_input)
                memory.add_message('assistant', response)

            print('\n')
        except Exception as e:
            print(str(e))
            modality = str(input('Por favor una modalidad de comunicación para esta sección (Texto o Audio): '))
    memory.close()
    agent_loop.close()

if __name__ == '__main__':
   asyncio.run(chat_cli())