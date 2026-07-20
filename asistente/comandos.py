import datetime
import webbrowser

import pyjokes
import pywhatkit
import wikipedia
import yfinance


class Comandos:
    """Interpreta el texto recibido y ejecuta la acción correspondiente."""

    def __init__(self, audio_output):
        self.audio_output = audio_output
        self.cartera = {
            "apple": "AAPL",
            "amazon": "AMZN",
            "google": "GOOGL",
        }

    def hablar(self, mensaje):
        self.audio_output.hablar(mensaje)

    def pedir_dia(self):
        dia = datetime.date.today()
        calendario = {
            0: "Lunes",
            1: "Martes",
            2: "Miércoles",
            3: "Jueves",
            4: "Viernes",
            5: "Sábado",
            6: "Domingo",
        }
        self.hablar(f"Hoy es {calendario[dia.weekday()]}")

    def pedir_hora(self):
        ahora = datetime.datetime.now()
        mensaje = (
            f"En este momento son las {ahora.hour} horas "
            f"con {ahora.minute} minutos y {ahora.second} segundos"
        )
        self.hablar(mensaje)

    def buscar_wikipedia(self, pedido):
        consulta = pedido.replace("busca en wikipedia", "").strip()
        self.hablar("Buscando eso en Wikipedia")
        wikipedia.set_lang("es")
        wikipedia.set_user_agent("AsistenteVirtualDonna/1.0")

        try:
            resultado = wikipedia.summary(consulta, sentences=1)
            self.hablar("Wikipedia dice lo siguiente:")
            self.hablar(resultado)
        except Exception as error:
            print(f"Error Wikipedia: {error}")
            self.hablar(
                "Lo siento, no pude encontrar información en Wikipedia"
            )

    def consultar_accion(self, pedido):
        accion = pedido.split("de")[-1].strip()

        try:
            simbolo = self.cartera[accion]
            datos = yfinance.Ticker(simbolo)
            precio = datos.info["regularMarketPrice"]
            self.hablar(
                f"La encontré, el precio de {accion} es {precio}"
            )
        except (KeyError, TypeError):
            self.hablar("Perdón, pero no la he encontrado")

    def ejecutar(self, pedido):
        pedido = pedido.lower().strip()

        if "abrir youtube" in pedido:
            self.hablar("Con gusto, estoy abriendo YouTube")
            webbrowser.open("https://www.youtube.com")

        elif "abrir el navegador" in pedido:
            self.hablar("Claro, estoy en eso")
            webbrowser.open("https://www.google.com")

        elif "qué día es hoy" in pedido:
            self.pedir_dia()

        elif "qué hora es" in pedido:
            self.pedir_hora()

        elif "busca en wikipedia" in pedido:
            self.buscar_wikipedia(pedido)

        elif "busca en internet" in pedido:
            consulta = pedido.replace("busca en internet", "").strip()
            self.hablar("Ya mismo estoy en eso")
            pywhatkit.search(consulta)
            self.hablar("Esto es lo que he encontrado")

        elif "reproducir" in pedido:
            self.hablar(
                "Buena elección, ahora comienzo a reproducirlo"
            )
            pywhatkit.playonyt(pedido)

        elif "broma" in pedido:
            self.hablar(pyjokes.get_joke("es"))

        elif "precio de las acciones" in pedido:
            self.consultar_accion(pedido)

        elif "adiós" in pedido:
            self.hablar(
                "Perfecto, me voy a descansar, cualquier cosa me avisas"
            )
            return False

        return True
