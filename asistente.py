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

import json
import platform
import webbrowser
from pathlib import Path

import pyjokes
import pyttsx3
import pywhatkit
import speech_recognition as sr
import wikipedia
import yfinance


def cargar_textos(idioma="es"):
    ruta = Path(__file__).parent / "idiomas" / f"{idioma}.json"

    with ruta.open("r", encoding="utf-8") as archivo:
        return json.load(archivo)


TEXTOS = cargar_textos()

VOZ_WINDOWS = (
    r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices"
    r"\Tokens\TTS_MS_ES-ES_HELENA_11.0"
)


def transformar_audio_en_texto():
    reconocedor = sr.Recognizer()

    with sr.Microphone() as origen:
        reconocedor.pause_threshold = 0.8
        print(TEXTOS["escucha"]["puedes_hablar"])
        audio = reconocedor.listen(origen)

    try:
        pedido = reconocedor.recognize_google(audio, language="es-AR")
        print(
            TEXTOS["escucha"]["dijiste"].format(pedido=pedido)
        )
        return pedido

    except sr.UnknownValueError:
        print(TEXTOS["escucha"]["no_entiendo"])

    except sr.RequestError:
        print(TEXTOS["escucha"]["sin_servicio"])

    except Exception as error:
        print(TEXTOS["escucha"]["error_general"])
        print(f"Detalle técnico: {error}")

    return TEXTOS["escucha"]["esperando"]


def hablar(mensaje):
    motor = pyttsx3.init()

    if platform.system() == "Windows":
        motor.setProperty("voice", VOZ_WINDOWS)

    motor.say(mensaje)
    motor.runAndWait()


def mostrar_ayuda():
    print(TEXTOS["respuestas"]["ayuda_titulo"])

    for comando in TEXTOS["comandos"]:
        print(f"- {comando}")


def pedir_dia():
    hoy = datetime.date.today()
    nombre_dia = TEXTOS["dias_semana"][hoy.weekday()]
    mensaje = TEXTOS["respuestas"]["dia"].format(dia=nombre_dia)

    print(mensaje)
    hablar(mensaje)


def pedir_hora():
    ahora = datetime.datetime.now()
    mensaje = TEXTOS["respuestas"]["hora"].format(
        hora=ahora.hour,
        minuto=ahora.minute,
        segundo=ahora.second,
    )

    print(mensaje)
    hablar(mensaje)


def saludo_inicial():
    hora = datetime.datetime.now().hour

    if hora < 6 or hora > 20:
        momento = TEXTOS["saludo"]["noche"]
    elif hora < 13:
        momento = TEXTOS["saludo"]["manana"]
    else:
        momento = TEXTOS["saludo"]["tarde"]

    mensaje = TEXTOS["saludo"]["presentacion"].format(
        momento=momento
    )
    hablar(mensaje)


def buscar_wikipedia(pedido):
    hablar(TEXTOS["respuestas"]["buscando_wikipedia"])
    consulta = pedido.replace("busca en wikipedia", "").strip()

    wikipedia.set_lang("es")
    wikipedia.set_user_agent("AsistenteVirtualDonna/1.0")

    try:
        resultado = wikipedia.summary(consulta, sentences=1)
        hablar(TEXTOS["respuestas"]["wikipedia_dice"])
        hablar(resultado)

    except Exception as error:
        print(f"Error Wikipedia: {error}")
        hablar(TEXTOS["respuestas"]["error_wikipedia"])


def consultar_accion(pedido):
    accion = pedido.split("de")[-1].strip()
    cartera = {
        "apple": "AAPL",
        "amazon": "AMZN",
        "google": "GOOGL",
    }

    try:
        simbolo = cartera[accion]
        datos = yfinance.Ticker(simbolo)
        precio = datos.info["regularMarketPrice"]
        mensaje = TEXTOS["respuestas"]["precio_accion"].format(
            accion=accion,
            precio=precio,
        )
        hablar(mensaje)

    except Exception:
        hablar(TEXTOS["respuestas"]["accion_no_encontrada"])


def pedir_cosas():
    saludo_inicial()
    continuar = True

    while continuar:
        pedido = transformar_audio_en_texto().lower()

        if "abrir youtube" in pedido:
            hablar(TEXTOS["respuestas"]["abrir_youtube"])
            webbrowser.open("https://www.youtube.com")

        elif "abrir el navegador" in pedido:
            hablar(TEXTOS["respuestas"]["abrir_navegador"])
            webbrowser.open("https://www.google.com")

        elif "qué día es hoy" in pedido:
            pedir_dia()

        elif "qué hora es" in pedido:
            pedir_hora()

        elif "busca en wikipedia" in pedido:
            buscar_wikipedia(pedido)

        elif "busca en internet" in pedido:
            hablar(TEXTOS["respuestas"]["buscando_internet"])
            consulta = pedido.replace(
                "busca en internet", ""
            ).strip()
            pywhatkit.search(consulta)
            hablar(TEXTOS["respuestas"]["resultado_internet"])

        elif "reproducir" in pedido:
            hablar(TEXTOS["respuestas"]["reproducir"])
            pywhatkit.playonyt(pedido)

        elif "broma" in pedido:
            hablar(pyjokes.get_joke("es"))

        elif "precio de las acciones" in pedido:
            consultar_accion(pedido)

        elif "ayuda" in pedido:
            mostrar_ayuda()

        elif "adiós" in pedido:
            hablar(TEXTOS["respuestas"]["despedida"])
            continuar = False


if __name__ == "__main__":
    pedir_cosas()

