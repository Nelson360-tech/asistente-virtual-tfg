import pyttsx3


class AudioOutput:
    """Convierte texto en voz mediante pyttsx3."""

    def __init__(self, voz_id=None, velocidad=175):
        self.motor = pyttsx3.init()
        self.motor.setProperty("rate", velocidad)

        if voz_id:
            self.motor.setProperty("voice", voz_id)

    def hablar(self, mensaje):
        print(f"Donna: {mensaje}")
        self.motor.say(mensaje)
        self.motor.runAndWait()
