import datetime

from .audio_input import AudioInput
from .audio_output import AudioOutput
from .comandos import Comandos


class Asistente:
    """Coordina la entrada, el procesamiento y la salida de audio."""

    def __init__(self, audio_input=None, audio_output=None):
        self.audio_input = audio_input or AudioInput()
        self.audio_output = audio_output or AudioOutput()
        self.comandos = Comandos(self.audio_output)

    def saludo_inicial(self):
        hora = datetime.datetime.now().hour

        if hora < 6 or hora > 20:
            momento = "Buenas noches"
        elif hora < 13:
            momento = "Buen día"
        else:
            momento = "Buenas tardes"

        self.audio_output.hablar(
            f"{momento}, soy Donna, tu asistente personal. "
            "Por favor, dime en qué te puedo ayudar"
        )

    def iniciar(self):
        self.saludo_inicial()
        continuar = True

        while continuar:
            pedido = self.audio_input.escuchar()
            continuar = self.comandos.ejecutar(pedido)
