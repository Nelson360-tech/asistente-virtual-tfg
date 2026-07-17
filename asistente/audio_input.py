import speech_recognition as sr


class AudioInput:
    """Escucha el micrófono y convierte la voz en texto."""

    def __init__(self, idioma="es-AR", pausa=0.8):
        self.idioma = idioma
        self.reconocedor = sr.Recognizer()
        self.reconocedor.pause_threshold = pausa

    def escuchar(self):
        with sr.Microphone() as origen:
            print("Ya puedes hablar")
            audio = self.reconocedor.listen(origen)

        try:
            pedido = self.reconocedor.recognize_google(
                audio,
                language=self.idioma
            )
            print(f"Dijiste: {pedido}")
            return pedido

        except sr.UnknownValueError:
            print("Uuppss, no entendí")
        except sr.RequestError:
            print("Uuppss, no hay servicio")
        except Exception as error:
            print(f"Uuppss, algo ha salido mal: {error}")

        return "Sigo esperando"
