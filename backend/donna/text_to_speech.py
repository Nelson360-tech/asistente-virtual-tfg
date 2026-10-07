import uuid
import wave
from pathlib import Path

from piper import PiperVoice


class TextToSpeech:
    """Turns text into a WAV file using a local Piper voice."""

    def __init__(self, voice_path, output_dir):
        self.voice = PiperVoice.load(voice_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def synthesize(self, text):
        filename = f"{uuid.uuid4().hex}.wav"
        with wave.open(str(self.output_dir / filename), "wb") as wav_file:
            self.voice.synthesize_wav(text, wav_file)
        return filename