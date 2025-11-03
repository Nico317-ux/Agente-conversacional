from AgentProject.core.audio_orchestrator.tts import ElevenLabsWebSocketTTS
import logging
from typing import Optional, AsyncGenerator
import asyncio
import threading
logging.basicConfig(
            level= logging.INFO,
            format= '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

logger = logging.getLogger(__name__)

class TTSManager:
    def __init__(self,
                 api_key: str,
                 voice_id: str):
        
        self._lock = asyncio.Lock()
        self.is_listening = False
        self.tts_engine = ElevenLabsWebSocketTTS(api_key= api_key, voice_id= voice_id)

    async def start_listening(self):
        async with self._lock:
            if not self.is_listening:
                await self.tts_engine.init_websocket()
                self.is_listening = True
    
    async def stop_listening(self):
        async with self._lock:
            if self.is_listening:
                await self.tts_engine.close()
                self.is_listening = False
    
    async def tts_processing(self, text_chunk: AsyncGenerator[str, None], interrupt_event: threading.Event):
        try:
            tts_task = asyncio.create_task(self.tts_engine.stream_tts(text_chunk= text_chunk, interrupt_event= interrupt_event))
            tts_transcription = await tts_task
            return tts_transcription
        except Exception as e:
            logger.error(f'Error en la generacion de respuesta: {str(e)}')