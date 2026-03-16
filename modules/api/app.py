from fastapi import FastAPI
from .routes.ingest import router as ingest_router

app = FastAPI(title="Opsight API", version="0.1")
app.include_router(ingest_router)

@app.get("/health")
def health():
    return {"status": "ok"}