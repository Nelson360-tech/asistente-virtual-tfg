import datetime

DAYS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


class Commands:
    """Maps a question to an answer and an optional action for the client."""

    def execute(self, question):
        text = question.lower()

        if "qué hora es" in text:
            now = datetime.datetime.now()
            return self._reply(f"Son las {now.hour} horas con {now.minute} minutos")

        if "qué día es" in text:
            today = datetime.date.today()
            return self._reply(f"Hoy es {DAYS[today.weekday()]}")

        if "abrir youtube" in text:
            action = {"type": "open_url", "url": "https://www.youtube.com"}
            return self._reply("Con gusto, estoy abriendo YouTube", action)

        return self._reply("Perdón, no entendí el pedido")

    def _reply(self, answer, action=None):
        return {"answer": answer, "action": action}