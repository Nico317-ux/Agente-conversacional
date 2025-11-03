import websockets
import pyaudio
import json
import asyncio
import base64
from typing import AsyncGenerator
from AgentProject.configuration.app_configuration.app_configuration import AppConfiguration
import logging
import threading

logging.basicConfig(
    level= logging.INFO,
    format= '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ElevenLabsWebSocketTTS:
    def __init__(self,
                 api_key: str,
                 voice_id: str,
                 model_id: str = 'eleven_multilingual_v2',
                 sample_rate: int = 24000,
                 output_format: str = 'pcm_24000'):
        
        self.api_key = api_key
        self.voice_id = voice_id
        self.model_id = model_id
        self.sample_rate = sample_rate
        self.output_format = output_format
        self.uri = f'wss://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream-input?model_id={self.model_id}&output_format={self.output_format}&inactivity_timeout=180'

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format= pyaudio.paInt16,
            channels= 1,
            rate = self.sample_rate,
            output= True,
            frames_per_buffer= 1024,
            stream_callback= None
        )

        self.websocket = None
        self.is_connected = False
        self._lock = asyncio.Lock()

    async def init_websocket(self):
        async with self._lock:
            if self.is_connected and self.websocket:
                try:
                    pong_waiter = await self.websocket.ping()
                    await asyncio.wait_for(pong_waiter, timeout=2.0)
                    return True
                except:
                    self.is_connected = False
                    await self._cleanup_websocket()
            
            if not self.is_connected:
                await self._connect()

    async def _connect(self):
        try:
            self.websocket = await websockets.connect(self.uri)
            init_message = {
                'text': ' ',
                'voice_settings': {'stability': 0.5, 
                                   'similarity_boost': 0.75,
                                   'use_speaker_boost': True},
                'generation_config': {
                    'chunk_length_schedule': [50,90,120],
                    'apply_text_normalization': 'auto'
                },
                'xi_api_key': self.api_key
            }

            await self.websocket.send(json.dumps(init_message))
            self.is_connected = True
            logger.info('Websocket elevenlabs inicilizado')
        except Exception as e:
            logger.error(f'Error en la conexion websocket: {str(e)}')
            self.is_connected = False
            raise
    
    async def _cleanup_websocket(self):
        if self.websocket:
            try:
                await self.websocket.close()
            except:
                pass
            self.websocket = None
        self.is_connected = False
        logger.info('Conexion websocket cerrada')

    async def stream_tts(self, text_chunk: AsyncGenerator[str, None], interrupt_event: threading.Event) -> str:
        
        transcription = ''
        await self.init_websocket()

        try:   
            async for chunk in text_chunk:
                transcription += chunk
                if chunk.strip():
                    text_message = {'text': chunk, 'try_trigger_generation': True}
                    await self.websocket.send(json.dumps(text_message))
            
            await self.websocket.send(json.dumps({'text': ''}))

            while True:
                if interrupt_event.is_set():
                    logger.info('Interrupcion detectada en el motor de TTS')
                    break
                try:
                    message_str = await asyncio.wait_for(self.websocket.recv(), timeout=0.1)
                    if message_str:
                        data = json.loads(message_str)
                        if 'audio' in data and data['audio']:
                            audio_chunk = base64.b64decode(data['audio'])
                            if len(audio_chunk) > 0:
                                self.stream.write(audio_chunk)
                        if data.get('isFinal'):
                            break
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    logger.error(f'Error en la recepcion de audio del websocket: {str(e)}')
                    break
        except websockets.exceptions.ConnectionClosed:
            logger.info('conexion cerrada por el servidor')
            await self._cleanup_websocket()
        except Exception as e:
            logger.error(f'Error durante el TTS steaming: {str(e)}')
            await self._cleanup_websocket()
            raise
        finally:
            return transcription

    async def close(self):
        if self.stream and self.stream.is_active():
            self.stream.stop_stream()
            logger.info('Se cerro conexion stream')
        await self._cleanup_websocket()
        if self.stream:
            self.stream.close()
        if self.p:
            self.p.terminate()
        logger.info('Todos los objetos de TTS han sido cerrados')