import datetime
import webbrowser

import pywhatkit
import pyjokes
import wikipedia
import yfinance

CALENDARIO = {
    0: 'Lunes',
    1: 'Martes',
    2: 'Miércoles',
    3: 'Jueves',
    4: 'Viernes',
    5: 'Sábado',
    6: 'Domingo',
}

CARTERA = {
    'apple': 'AAPL',
    'amazon': 'AMZN',
    'google': 'GOOGL',
}


class Comandos:
    """Contiene todas las acciones que Donna puede ejecutar.

    Cada método hace UNA cosa y recibe un AudioOutput para poder
    responder por voz.
    """

    def __init__(self, audio_output):
        self.audio_output = audio_output

    def decir_dia(self):
        dia = datetime.date.today()
        dia_semana = dia.weekday()
        self.audio_output.hablar(f'Hoy es {CALENDARIO[dia_semana]}')

    def decir_hora(self):
        hora = datetime.datetime.now()
        mensaje = (
            f'En este momento son las {hora.hour} horas con '
            f'{hora.minute} minutos y {hora.second} segundos'
        )
        print(mensaje)
        self.audio_output.hablar(mensaje)

    def abrir_youtube(self):
        self.audio_output.hablar('Con gusto, estoy abriendo youTube')
        webbrowser.open('https://www.youtube.com')

    def abrir_navegador(self):
        self.audio_output.hablar('Claro, estoy en eso')
        webbrowser.open('https://www.google.com')

    def buscar_wikipedia(self, pedido):
        self.audio_output.hablar('Buscando eso en wikipedia')
        termino = pedido.replace('busca en wikipedia', '').strip()
        wikipedia.set_lang('es')
        wikipedia.set_user_agent('AsistenteVirtualDonna/1.0')
        try:
            resultado = wikipedia.summary(termino, sentences=1)
            self.audio_output.hablar('Wikipedia dice lo siguiente:')
            self.audio_output.hablar(resultado)
        except Exception as e:
            print(f'Error Wikipedia: {e}')
            self.audio_output.hablar('Lo siento, no pude encontrar información en Wikipedia')

    def buscar_internet(self, pedido):
        self.audio_output.hablar('Ya mismo estoy en eso')
        termino = pedido.replace('busca en internet', '').strip()
        pywhatkit.search(termino)
        self.audio_output.hablar('Esto es lo que he encontrado')

    def reproducir(self, pedido):
        self.audio_output.hablar('Buena elección, ahora comienzo a reproducirlo')
        pywhatkit.playonyt(pedido)

    def contar_broma(self):
        self.audio_output.hablar(pyjokes.get_joke('es'))

    def precio_acciones(self, pedido):
        accion = pedido.split('de')[-1].strip()
        try:
            ticker = CARTERA[accion]
            accion_buscada = yfinance.Ticker(ticker)
            precio_actual = accion_buscada.info['regularMarketPrice']
            self.audio_output.hablar(f'La encontré, el precio de {accion} es {precio_actual}')
        except Exception:
            self.audio_output.hablar('Perdón, pero no la he encontrado')

    def despedirse(self):
        self.audio_output.hablar('Perfecto, me voy a descansar, cualquier cosa me avisas')
