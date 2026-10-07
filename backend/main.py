from fastapi import FastAPI, UploadFile

from donna.speech_to_text import SpeechToText

app = FastAPI(title="Donna API")
stt = SpeechToText()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/ask")
def ask(audio: UploadFile):
    question = stt.transcribe(audio.file)
    return {"question": question}
