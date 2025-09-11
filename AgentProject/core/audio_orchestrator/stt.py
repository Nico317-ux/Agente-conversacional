import sounddevice as sd # Para captura de audio
import numpy as np # Buffer management
import soundfile as sf # Convert to FLAC
from io import BytesIO # RAM storage
from huggingface_hub import InferenceClient

class SpeechToText:
    def __init__(self, provider: str, hf_token: str, sample_rate: int = 44100, name_model:str = 'openai/whisper-large-v3'):
        self.sample_rate = sample_rate
        self.recording = []
        self.is_recording = False
        self.client = InferenceClient(
            provider= provider,
            api_key= hf_token
        )
        self.name_model = name_model
    
    def start(self):
        #Start background recording
        self.is_recording = True

        def callback(indata, frames, time, status):
            if self.is_recording:
                self.recording.append(indata.copy()) # Stores audio chunks
        
        self.stream = sd.InputStream(
            samplerate= self.sample_rate,
            channels= 1,
            dtype= 'float32',
            callback= callback
        )
        self.stream.start()
    
    def stop(self) -> str:
        #Stop recording and return FLAC to RAM
        if self.stream:
            self.stream.stop()
            self.stream.close()
        
        # Combine all audio chunks
        audio_data = np.concatenate(self.recording)
        #Drop content in the recording
        self.recording = []

        # Convert to FLAC in memory (without touching disk)
        buffer = BytesIO()
        sf.write(
            buffer,
            audio_data,
            self.sample_rate,
            format = 'FLAC'
        )
        buffer.seek(0)
        return str(self.client.automatic_speech_recognition(
            buffer.getvalue(),
            model= self.name_model
        )['text'])
    