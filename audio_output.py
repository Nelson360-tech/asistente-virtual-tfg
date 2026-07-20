import pyttsx3

# IDs de voces disponibles en Windows (Microsoft Speech)
VOZ_ES_HELENA = r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_ES-ES_HELENA_11.0'
VOZ_EN_ZIRA = r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0'
VOZ_EN_DAVID = r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_DAVID_11.0'


class AudioOutput:
    """Se encarga de que el asistente pueda hablar (texto a voz)."""

    def __init__(self, voice_id=VOZ_ES_HELENA):
        self.voice_id = voice_id

    def hablar(self, mensaje):
        """Reproduce por voz el mensaje recibido."""
        engine = pyttsx3.init()
        engine.setProperty('voice', self.voice_id)
        engine.say(mensaje)
        engine.runAndWait()
