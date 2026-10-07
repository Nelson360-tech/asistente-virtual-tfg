from fastapi import FastAPI, UploadFile
from donna.commands import Commands

from donna.speech_to_text import SpeechToText

app = FastAPI(title="Donna API")
stt = SpeechToText()
commands = Commands()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/ask")
def ask(audio: UploadFile):
    question = stt.transcribe(audio.file)
    result = commands.execute(question)
    return {
        "question": question,
        "answer": result["answer"],
        "action": result["action"],
    }