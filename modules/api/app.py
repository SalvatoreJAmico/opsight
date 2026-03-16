from fastapi import FastAPI
from .routes.ingest import router as ingest_router
from .routes.entities import router as entities_router
from modules.api.errors import register_error_handlers





app = FastAPI(title="Opsight API", version="0.1")
app.include_router(ingest_router)
app.include_router(entities_router)
from .routes.status import router as status_router
app.include_router(status_router)
register_error_handlers(app)





@app.get("/health")
def health():
    return {"status": "ok"}

