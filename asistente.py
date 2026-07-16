import datetime

from audio_input import AudioInput
from audio_output import AudioOutput
from comandos import Comandos


class Asistente:
    """Orquesta todo: escucha, interpreta el pedido y ejecuta el comando."""

    def __init__(self, nombre="Donna"):
        self.nombre = nombre
        self.audio_input = AudioInput()
        self.audio_output = AudioOutput()
        self.comandos = Comandos(self.audio_output)

    def saludo_inicial(self):
        hora = datetime.datetime.now()
        if hora.hour < 6 or hora.hour > 20:
            momento = 'Buenas noches'
        elif 6 <= hora.hour < 13:
            momento = 'Buen día'
        else:
            momento = 'Buenas tardes'
        self.audio_output.hablar(
            f'{momento}, soy {self.nombre}, tu asistente personal. '
            'Por favor, dime en que te puedo ayudar'
        )

    def procesar_pedido(self, pedido):
        """Interpreta el pedido y devuelve False si hay que cortar el loop."""
        if 'abrir youtube' in pedido:
            self.comandos.abrir_youtube()
        elif 'abrir el navegador' in pedido:
            self.comandos.abrir_navegador()
        elif 'qué día es hoy' in pedido:
            self.comandos.decir_dia()
        elif 'qué hora es' in pedido:
            self.comandos.decir_hora()
        elif 'busca en wikipedia' in pedido:
            self.comandos.buscar_wikipedia(pedido)
        elif 'busca en internet' in pedido:
            self.comandos.buscar_internet(pedido)
        elif 'reproducir' in pedido:
            self.comandos.reproducir(pedido)
        elif 'broma' in pedido:
            self.comandos.contar_broma()
        elif 'precio de las acciones' in pedido:
            self.comandos.precio_acciones(pedido)
        elif 'adiós' in pedido:
            self.comandos.despedirse()
            return False
        return True

    def ejecutar(self):
        self.saludo_inicial()
        continuar = True
        while continuar:
            pedido = self.audio_input.escuchar().lower()
            continuar = self.procesar_pedido(pedido)
