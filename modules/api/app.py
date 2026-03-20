import logging
import time
import pandas as pd
from pathlib import Path

from fastapi import FastAPI
from fastapi import Request

from modules.config.logging_config import setup_logging
from modules.config.runtime_config import load_runtime_config
from modules.api.errors import register_error_handlers
from modules.visualization.plots import create_histogram
from modules.persistence.persistence_manager import PersistenceManager
from fastapi.staticfiles import StaticFiles

setup_logging(service_name="opsight.api")
logger = logging.getLogger("opsight.api")

try:
    runtime_config = load_runtime_config()
except Exception as exc:
    logger.error(
        "Runtime config load failed during API startup",
        extra={
            "event": "runtime_config_error",
            "error_type": "runtime_config_error",
            "error_message": str(exc),
        },
    )
    raise

logger.info(
    "Runtime configuration loaded",
    extra={
        "event": "runtime_config_loaded",
        "app_env": runtime_config.app_env,
        "app_version": runtime_config.app_version,
        "persistence_mode": runtime_config.persistence_mode,
        "port": runtime_config.port,
    },
)

logger.info(
    "API startup configuration loaded",
    extra={
        "event": "api_startup",
        "app_env": runtime_config.app_env,
        "app_version": runtime_config.app_version,
        "persistence_mode": runtime_config.persistence_mode,
        "port": runtime_config.port,
    },
)

from .routes.ingest import router as ingest_router
from .routes.entities import router as entities_router
from .routes.status import router as status_router

# Setup static files directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = PROJECT_ROOT / "static"
STATIC_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Opsight API", version=runtime_config.app_version)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(ingest_router)
app.include_router(entities_router)
app.include_router(status_router)
register_error_handlers(app)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    logger.info(
        "Request started",
        extra={
            "event": "request_started",
            "method": request.method,
            "path": request.url.path,
        },
    )
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "Request failed",
            extra={
                "event": "request_failed",
                "method": request.method,
                "path": request.url.path,
            },
        )
        raise

    runtime_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        "Request completed",
        extra={
            "event": "request_completed",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "runtime_ms": runtime_ms,
        },
    )
    return response

@app.get("/charts/histogram")
def histogram():
    try:
        manager = PersistenceManager(runtime_config)
        records = manager.retrieve_all()

        if not records:
            return {"error": "No records available for visualization"}

        df = pd.DataFrame(records)
        path = create_histogram(df)
        return {"image": path}
    except Exception as exc:
        logger.error(f"Histogram generation failed: {str(exc)}")
        return {"error": str(exc)}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": runtime_config.app_version,
    }

