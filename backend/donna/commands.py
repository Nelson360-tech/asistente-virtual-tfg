import datetime
import unicodedata

DAYS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def normalize(text):
    """Lowercases the text and removes accents, so 'Qué Día' matches 'que dia'."""
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


class Commands:
    """Maps a question to an answer and an optional action for the client."""

    def execute(self, question):
        text = normalize(question)

        if "que hora" in text:
            now = datetime.datetime.now()
            return self._reply(f"Son las {now.hour} horas con {now.minute} minutos")

        if "que dia" in text:
            today = datetime.date.today()
            return self._reply(f"Hoy es {DAYS[today.weekday()]}")

        if "abrir youtube" in text or "abre youtube" in text:
            action = {"type": "open_url", "url": "https://www.youtube.com"}
            return self._reply("Con gusto, estoy abriendo YouTube", action)

        return self._reply("Perdón, no entendí el pedido")

    def _reply(self, answer, action=None):
        return {"answer": answer, "action": action}