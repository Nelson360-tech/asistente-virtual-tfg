import uuid
import wave
from pathlib import Path

from piper import PiperVoice


class TextToSpeech:
    """Turns text into a WAV file and reports the timing of each phoneme."""

    def __init__(self, voice_path, output_dir):
        self.voice = PiperVoice.load(voice_path, include_alignments=True)
        self.sample_rate = self.voice.config.sample_rate
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def synthesize(self, text):
        filename = f"{uuid.uuid4().hex}.wav"
        with wave.open(str(self.output_dir / filename), "wb") as wav_file:
            alignments = self.voice.synthesize_wav(
                text, wav_file, include_alignments=True
            )
        return filename, alignments or []