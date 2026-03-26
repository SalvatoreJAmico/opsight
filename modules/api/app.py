import logging
import time
import pandas as pd
from pathlib import Path

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request

from modules.config.logging_config import setup_logging
from modules.config.runtime_config import load_runtime_config
from modules.api.session_state import reset_session_state
from modules.api.session_state import get_session_state
from modules.api.errors import register_error_handlers
from modules.persistence.persistence_manager import PersistenceManager
from fastapi.staticfiles import StaticFiles
from modules.config.storage_config import StorageConfig
from modules.persistence.local_storage import LocalStorage
from modules.visualization.plots import (
    create_histogram,
    create_bar_category_chart,
    create_boxplot,
    create_scatter_plot,
    create_grouped_comparison_chart,
)


def _records_to_chart_df(records: list) -> pd.DataFrame:
    """Flatten canonical records into a chart-ready DataFrame.

    Maps the first numeric feature to ``metric_value``, the second to
    ``secondary_metric``, and the first string feature to ``category``.
    Falls back to ``entity_id`` when a column is not available.
    """
    rows = []
    for r in records:
        row = {"entity_id": r.get("entity_id", "")}
        row.update(r.get("features", {}))
        rows.append(row)

    df = pd.DataFrame(rows)

    num_cols = [
        c for c in df.columns
        if c != "entity_id" and pd.api.types.is_numeric_dtype(df[c])
    ]
    str_cols = [
        c for c in df.columns
        if c != "entity_id" and not pd.api.types.is_numeric_dtype(df[c])
    ]

    df["metric_value"] = df[num_cols[0]] if len(num_cols) >= 1 else 0.0
    df["secondary_metric"] = df[num_cols[1]] if len(num_cols) >= 2 else df["metric_value"]
    df["category"] = df[str_cols[0]] if str_cols else df["entity_id"]

    return df


def get_chart_dataframe() -> pd.DataFrame:
    """Load the active persisted records and return a chart-ready DataFrame.

    Raises HTTPException 422 when no records have been persisted yet.
    """
    config = StorageConfig()
    storage = LocalStorage(storage_path=config.storage_path)
    records = storage.load_records()

    if not records:
        raise HTTPException(
            status_code=422,
            detail="No dataset loaded. Upload and run a dataset to view charts.",
        )

    return _records_to_chart_df(records)


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
from modules.api.routes.ml import router as ml_router

app.include_router(ml_router)


@app.on_event("startup")
def reset_in_memory_session_state() -> None:
    reset_session_state()

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
        df = get_chart_dataframe()
        path = create_histogram(df)
        return {"image": path}
    except Exception as exc:
        logger.error(f"Histogram generation failed: {str(exc)}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/charts/bar-category")
def bar_category():
    try:
        df = get_chart_dataframe()
        path = create_bar_category_chart(df)
        return {"image": path}
    except Exception as exc:
        logger.error(f"Bar chart generation failed: {str(exc)}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/charts/boxplot")
def boxplot():
    try:
        df = get_chart_dataframe()
        path = create_boxplot(df)
        return {"image": path}
    except Exception as exc:
        logger.error(f"Box plot generation failed: {str(exc)}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/charts/scatter")
def scatter():
    try:
        df = get_chart_dataframe()
        path = create_scatter_plot(df)
        return {"image": path}
    except Exception as exc:
        logger.error(f"Scatter plot generation failed: {str(exc)}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/charts/grouped-comparison")
def grouped_comparison():
    try:
        df = get_chart_dataframe()
        path = create_grouped_comparison_chart(df)
        return {"image": path}
    except Exception as exc:
        logger.error(f"Grouped comparison chart generation failed: {str(exc)}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": runtime_config.app_version,
    }


@app.get("/charts/overview")
def charts_overview():
    config = StorageConfig()
    storage = LocalStorage(storage_path=config.storage_path)
    records = storage.load_records()

    if not records:
        raise HTTPException(
            status_code=422,
            detail="No dataset loaded. Upload and run a dataset to view charts.",
        )

    session = get_session_state()
    active_dataset = session.get("active_dataset") or "unknown"

    rows = []
    for r in records:
        row = {"entity_id": r.get("entity_id", "")}
        row.update(r.get("features", {}))
        rows.append(row)

    df = pd.DataFrame(rows)

    num_cols = [
        c for c in df.columns
        if c != "entity_id" and pd.api.types.is_numeric_dtype(df[c])
    ]

    stats: dict = {}
    if num_cols:
        series = df[num_cols[0]].dropna()
        if len(series) > 0:
            stats = {
                "min": round(float(series.min()), 4),
                "max": round(float(series.max()), 4),
                "mean": round(float(series.mean()), 4),
                "count": int(len(series)),
            }

    return {
        "source": active_dataset,
        "rows": len(df),
        "variables": len(df.columns),
        "fields": list(df.columns),
        **stats,
    }

