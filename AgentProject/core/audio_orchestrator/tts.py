from elevenlabs.client import ElevenLabs
from elevenlabs import stream

class TextToSpeech:
    def __init__(self,
                 api_key: str,
                 voice_id: str,
                 model_id: str = 'eleven_turbo_v2_5'):
        
        self.model_id = model_id
        self.voice_id = voice_id
        self.clien = ElevenLabs(
            api_key= api_key
        )
    
    def text_reproduction(self, text: str) -> None:

        audio_stream = self.clien.text_to_speech.stream(
            text= text,
            voice_id= self.voice_id,
            model_id= self.model_id
        )
        stream(audio_stream)