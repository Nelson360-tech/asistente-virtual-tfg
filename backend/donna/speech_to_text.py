from faster_whisper import WhisperModel


class SpeechToText:
    """Converts an audio file into text using a local Whisper model."""

    def __init__(self, model_size="base"):
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def transcribe(self, audio_file, language="es"):
        segments, _ = self.model.transcribe(audio_file, language=language)
        return " ".join(segment.text.strip() for segment in segments)