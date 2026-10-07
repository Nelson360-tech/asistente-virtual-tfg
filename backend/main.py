from fastapi import FastAPI

app = FastAPI(title="Donna API")


@app.get("/health")
def health():
    return {"status": "ok"}