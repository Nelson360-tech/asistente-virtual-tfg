from pathlib import Path

from fastapi import FastAPI, UploadFile
from fastapi.staticfiles import StaticFiles

from donna.commands import Commands
from donna.speech_to_text import SpeechToText
from donna.text_to_speech import TextToSpeech

BASE_DIR = Path(__file__).parent
AUDIO_DIR = BASE_DIR / "audio"
VOICE_PATH = BASE_DIR / "voices" / "es_AR-daniela-high.onnx"

app = FastAPI(title="Donna API")
stt = SpeechToText()
commands = Commands()
tts = TextToSpeech(VOICE_PATH, AUDIO_DIR)

app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/ask")
def ask(audio: UploadFile):
    question = stt.transcribe(audio.file)
    result = commands.execute(question)
    filename = tts.synthesize(result["answer"])
    return {
        "question": question,
        "answer": result["answer"],
        "audio_url": f"/audio/{filename}",
        "action": result["action"],
    }