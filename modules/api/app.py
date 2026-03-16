from fastapi import FastAPI

app = FastAPI(title="Opsight API", version="0.1")


@app.get("/health")
def health():
    return {"status": "ok"}