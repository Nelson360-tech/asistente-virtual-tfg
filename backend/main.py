from fastapi import FastAPI, UploadFile

app = FastAPI(title="Donna API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/ask")
async def ask(audio: UploadFile):
    content = await audio.read()
    return {
        "filename": audio.filename,
        "content_type": audio.content_type,
        "size_bytes": len(content),
    }