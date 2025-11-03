import numpy as np
from typing import Callable, Optional
import queue
import threading
import sounddevice as sd
from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType
import logging
import asyncio


logging.basicConfig(
            level= logging.INFO,
            format= '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

logger = logging.getLogger(__name__)

class DeepgramStreamingSTT:
    def __init__(self,
                deepgram_api_key: str,
                callback: Callable,
                sample_rate: int = 16000,
                channels: int = 1,
                blocksize: int = 4096,
                model_name: str = 'nova-3',
                language: str = 'es'):
        
        self.deepgram_api_key = deepgram_api_key
        self.blocksize = blocksize
        self.callback = callback
        self.is_recording = False
        self.channels = channels
        self.sample_rate = sample_rate
        self.model_name = model_name
        self.language = language
        self._listen_task: Optional[asyncio.Task] = None
        self.audio_queue = queue.Queue()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None

    def _audio_callback(self, indata, frames, time, status) -> None:
        if not self.is_recording:
            return
        audio_data_16 = (indata * 32767).astype(np.int16)
        try:
            self.audio_queue.put(audio_data_16.tobytes())
        except Exception as e:
            logger.error(f'Error al colocar audio en cola: {str(e)}')

    def start_recording(self) -> None:
        if self.is_recording:
            return
        
        try:
            self.stream = sd.InputStream(
                blocksize= self.blocksize,
                callback= self._audio_callback,
                channels= self.channels,
                samplerate= self.sample_rate,
                dtype= 'float32'
            )
            self._loop = asyncio.new_event_loop()
            self._thread = threading.Thread(target=self._run_async_loop, daemon=True)
            self._thread.start()
            self.stream.start()
            self.is_recording = True
            logger.info('Streaming de audio iniciado')
        except Exception as e:
            logger.error(f'Error al Inicializar el Streaming: {str(e)} ')

    def stop_recording(self) -> None:
        if not self.is_recording:
            return
        
        self.is_recording = False
        if hasattr(self, 'stream') and self.stream:
            try:
                logger.info('Se cerro el Stream')
                self.stream.stop()
                self.stream.close()
            except:
                logger.error('Error al Cerrar el Stream')

        if self._loop and self._loop.is_running():
            try:
                self._loop.call_soon_threadsafe(self._cancel_listening)
                logger.info('Loop de evento STT cerrado')
            except:
                logger.error('Error al cerrar loop de eventos')
        if self._thread:
            self._thread.join(timeout=2.0)
            logger.info('Deepgram streaming detenido')
    
    def _cancel_listening(self):
        if hasattr(self, '_listen_task') and self._listen_task:
            self._listen_task.cancel()

    def _run_async_loop(self):
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._stream_audio_to_deepgram())
        except Exception as e:
            logger.error(f'Error en loop asincrono: {str(e)}')
    
    async def _stream_audio_to_deepgram(self):
        client = AsyncDeepgramClient(api_key=self.deepgram_api_key)

        try:
            async with client.listen.v1.connect(
                model=self.model_name, 
                language=self.language,
                encoding='linear16', 
                channels=self.channels,
                sample_rate=str(self.sample_rate),
                interim_results=True,
                vad_events=True,
                smart_format=True,
                endpointing=400
            ) as connection:

                connection.on(EventType.OPEN, lambda _: logger.info("Conexión abierta con Deepgram"))
                connection.on(EventType.MESSAGE, self.callback)
                connection.on(EventType.CLOSE, lambda _: logger.info("Conexión cerrada"))
                connection.on(EventType.ERROR, lambda error: logger.error(f"Error de Deepgram: {error}"))

                self._listen_task = asyncio.create_task(connection.start_listening())

                loop = asyncio.get_event_loop()
                while self.is_recording:
                    try:
                        chunk = await loop.run_in_executor(None, self.audio_queue.get, True, 0.1)
                        await connection._send(chunk)
                    except queue.Empty:
                        continue
                
                if self._listen_task:
                    try:
                        await self._listen_task
                    except asyncio.CancelledError:
                        pass
        
        except Exception as e:
            logger.error(f'Error en conexion Deepgram: {str(e)}')

    def stop_microphone(self):
        if hasattr(self, 'stream') and self.stream:
            try:
                logger.info('Se pauso el microfono')
                self.stream.stop()
            except Exception as e:
                logger.error(f'Error al pausar el microfono: {str(e)}')
    
    def start_microphone(self):
        if hasattr(self, 'stream') and self.stream:
            try:
                logger.info('Se inicio el microfono')
                self.stream.start()
            except Exception as e:
                logger.error(f'Error al inicial el microfono: {str(e)}')
            