import time
from pathlib import Path

from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from donna.commands import Commands
from donna.history import History
from donna.lip_sync import LipSync
from donna.speech_to_text import SpeechToText
from donna.text_to_speech import TextToSpeech

BASE_DIR = Path(__file__).parent
AUDIO_DIR = BASE_DIR / "audio"
VOICE_PATH = BASE_DIR / "voices" / "es_AR-daniela-high.onnx"
DB_PATH = BASE_DIR / "donna.db"

app = FastAPI(title="Donna API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

stt = SpeechToText()
commands = Commands()
tts = TextToSpeech(VOICE_PATH, AUDIO_DIR)
lip_sync = LipSync()
history = History(DB_PATH)

app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")


def elapsed_ms(start, end):
    return round((end - start) * 1000)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/ask")
def ask(audio: UploadFile):
    start = time.perf_counter()
    question = stt.transcribe(audio.file)
    after_stt = time.perf_counter()

    result = commands.execute(question)
    filename, alignments = tts.synthesize(result["answer"])
    after_tts = time.perf_counter()

    visemes = lip_sync.visemes(alignments, tts.sample_rate)
    end = time.perf_counter()

    history.add(
        question,
        result["answer"],
        filename,
        elapsed_ms(start, after_stt),
        elapsed_ms(after_stt, after_tts),
        elapsed_ms(start, end),
    )

    return {
        "question": question,
        "answer": result["answer"],
        "audio_url": f"/audio/{filename}",
        "visemes": visemes,
        "action": result["action"],
    }


@app.get("/api/history")
def get_history(limit: int = 20):
    return history.latest(limit)