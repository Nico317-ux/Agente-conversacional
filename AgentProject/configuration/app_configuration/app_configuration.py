from pydantic_settings import BaseSettings, SettingsConfigDict

class AppConfiguration(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    #API KEY and Database
    HF_TOKEN: str
    ELEVELABS_TOKEN: str
    DB_PATH_CONTEXT_MEMORY: str
    DB_PATH_EMBEDDING_CACHE: str
    DB_PATH_VECTO_RAG: str
    DEEPGRAM_API_KEY: str
    ASSEMBLYAI: str

    #Models
    LLM_MODEL_NAME: str = 'openai/gpt-oss-20b'
    EMBEDDING_MODEL_NAME: str = 'BAAI/bge-base-en-v1.5'
    STT_MODEL_NAME: str = 'openai/whisper-large-v3'

    #Provider
    LLM_PROVIDER: str = 'novita'
    EMBEDDING_PROVIDER: str = 'hf-inference'
    STT_MODEL_PROVIDER: str = 'fal-ai'

    #Elevelabs
    ELEVELABS_VOICE_ID: str ='86V9x9hrQds83qf7zaGn'

    #parameters of models
    SYSTEM_PROMPT: str = ''' 
        Eres un asistente conversacional diseñado para interactuar de forma natural, breve y eficaz, como lo haría un colega humano en una conversación real.

        **Tu estilo es:**
        - **Directo y claro**: Ve al grano. Responde la pregunta principal en la primera frase.
        - **Brevísima**: Tus respuestas normales tienen 1-3 frases. Evita preámbulos, explicaciones innecesarias y monólogos.
        - **Conversacional**: Usa un lenguaje coloquial y fluido. Es perfectamente válido responder con frases como "Vale", "Entendido", "Claro" o "Listo".
        - **Interactivo**: Después de dar tu respuesta, devuelve el turno al usuario. Si es relevante, invítalo a profundizar con una pregunta corta (ej: "¿Quieres más detalles?", "¿Te sirve así?").

        **Solo da respuestas largas si:**
        - El usuario lo pide explícitamente ("explícame en detalle", "escribe un correo", etc.).
        - La tarea lo requiere (generar un poema, un código, un resumen largo).

        **Nunca hables como una enciclopedia.** Tu objetivo es mantener un diálogo ágil y humano, no demostrar todo tu conocimiento de una sola vez.
'''

    
    LLM_MODEL_TEMPERATURE: float = 0.6
    LLM_MODEL_MAX_TOKENS: int = 65536
    DEFAULT_MAX_TOKENS_MEMORIE_CONTEXT: int = 8000
    RAG_TOP_K: int = 5
    RAG_SCORE_THRESHOLD: float = 0.68

    #mcp path config
    MCP_CONFIGURATION_JSON_PATH: str = 'AgentProject\\configuration\\mcp_configuration\\mcp_configuration.json' 

    #personality config
    GENDER_PERSONALITY: str = 'feminine'
    