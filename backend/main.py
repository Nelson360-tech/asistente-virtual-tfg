from pathlib import Path

from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from donna.commands import Commands
from donna.lip_sync import LipSync
from donna.speech_to_text import SpeechToText
from donna.text_to_speech import TextToSpeech

BASE_DIR = Path(__file__).parent
AUDIO_DIR = BASE_DIR / "audio"
VOICE_PATH = BASE_DIR / "voices" / "es_AR-daniela-high.onnx"

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

app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/ask")
def ask(audio: UploadFile):
    question = stt.transcribe(audio.file)
    result = commands.execute(question)
    filename, alignments = tts.synthesize(result["answer"])
    return {
        "question": question,
        "answer": result["answer"],
        "audio_url": f"/audio/{filename}",
        "visemes": lip_sync.visemes(alignments, tts.sample_rate),
        "action": result["action"],
    }