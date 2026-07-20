import speech_recognition as sr


class AudioInput:
    """Se encarga de escuchar el micrófono y transformar el audio en texto."""

    def __init__(self, idioma="es-AR", pause_threshold=0.8):
        self.recognizer = sr.Recognizer()
        self.idioma = idioma
        self.recognizer.pause_threshold = pause_threshold

    def escuchar(self):
        """Activa el micrófono, escucha y devuelve lo dicho como texto."""
        with sr.Microphone() as origen:
            print("Ya puedes hablar")
            audio = self.recognizer.listen(origen)
            try:
                pedido = self.recognizer.recognize_google(audio, language=self.idioma)
                print("Dijiste: " + pedido)
                return pedido
            except sr.UnknownValueError:
                print("Uuppss, no entendi")
                return "Sigo esperando"
            except sr.RequestError:
                print("Uuppss, no hay servicio")
                return "Sigo esperando"
            except Exception:
                print("Uuppss, algo ha salido mal")
                return "Sigo esperando"
