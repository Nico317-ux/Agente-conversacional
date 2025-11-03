import logging
from AgentProject.core.audio_orchestrator.stt_streaming import DeepgramStreamingSTT
from deepgram.extensions.types.sockets import ListenV1SocketClientResponse
import threading
import queue
from typing import Optional, Tuple

logging.basicConfig(
            level= logging.INFO,
            format= '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

logger = logging.getLogger(__name__)

class STTManager:
    def __init__(self, deepgram_api_key: str) -> None:
        self.transcription_queue = queue.Queue(maxsize=1)
        self.is_listening = False
        self.lock = threading.Lock()
        self.interruption_flag = threading.Event()
        self.microphone_flag = False

        def _put_in_queue(transcription_queue: queue.Queue, item: Tuple):
            try:
                transcription_queue.put_nowait(item)
            except queue.Full:
                try:
                    transcription_queue.get_nowait()
                except queue.Empty:
                    pass
                transcription_queue.put_nowait(item)
            finally:
                self._signal_interruption()
                logger.info('Se levanto la bandera')

        def transcription_callback(msg: ListenV1SocketClientResponse):
            try:
                if hasattr(msg, 'channel') and hasattr(msg.channel, 'alternatives') and len(msg.channel.alternatives) > 0:
                    sentence = msg.channel.alternatives[0].transcript
                    if len(sentence.strip()) > 0:
                        is_final = getattr(msg, 'is_final', False)
                        new_item = (is_final, sentence)
                        _put_in_queue(self.transcription_queue, new_item)
            except Exception as e:
                logger.error(f'Error en callback de transcription: {str(e)}')

        self.stt_engine = DeepgramStreamingSTT(
            deepgram_api_key= deepgram_api_key,
            callback= transcription_callback)

    def start_listening(self):
        with self.lock:
            if not self.is_listening:
                self.stt_engine.start_recording()
                self.is_listening = True
                self.microphone_flag = True
                logger.info('Servicio de escucha iniciado')
        
    def stop_listening(self):
        with self.lock:
            if self.is_listening:
                self.stt_engine.stop_recording()
                self.is_listening = False
                self.microphone_flag = False
                logger.info('Servicio de escucha detenido')

    def get_transcription(self, timeout: float = 0.1) -> Optional[Tuple[bool, str]]:
        try:
            transcription = self.transcription_queue.get(timeout= timeout)
            self.transcription_queue.task_done()
            return transcription
        except queue.Empty:
            return None
        except Exception as e:
            logger.error(f'Error en la obtencion de la transcripcion {str(e)}')
        
    def _signal_interruption(self):
        if not self.interruption_flag.is_set():
            self.interruption_flag.set()
    
    def check_interruption(self) -> bool:
        return self.interruption_flag.is_set()
    
    def clear_interruption(self):
        if self.interruption_flag.is_set():
            self.interruption_flag.clear()
            logger.info('Se limpio la bandera')
    
    def stop_microphone(self):
        if self.microphone_flag:
            self.stt_engine.stop_microphone()
            self.microphone_flag = False
            logger.info(f'Se pauso el microfono')
    
    def start_microphone(self):
        if not self.microphone_flag:
            self.stt_engine.start_microphone()
            self.microphone_flag = True
            logger.info('Se inicio el microfono')


if __name__ == '__main__':
    from AgentProject.configuration.app_configuration.app_configuration import AppConfiguration

    app_config = AppConfiguration() 

    def main(deepgram_key):
        stt_manager = STTManager(deepgram_key)
        try:
            stt_manager.start_listening()
            while True:
                result = stt_manager.get_transcription()
                if isinstance(result, tuple):
                    state, sentence = result
                    if state:
                        print(sentence)
                    else:
                        print(sentence)
                else:
                    continue
        except Exception as e:
            logger.info(f'Error: {str(e)}')
        except KeyboardInterrupt:
            pass
        finally:
            stt_manager.stop_listening()

    main(deepgram_key= app_config.DEEPGRAM_API_KEY)

        