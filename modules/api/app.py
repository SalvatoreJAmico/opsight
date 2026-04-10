import logging
import time
import pandas as pd
from pathlib import Path

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware

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


def _build_chart_context(df: pd.DataFrame) -> dict:
    """Return per-chart field-role context from the active dataset."""
    num_cols = [
        c for c in df.columns
        if c != "entity_id" and pd.api.types.is_numeric_dtype(df[c])
    ]
    str_cols = [
        c for c in df.columns
        if c != "entity_id" and not pd.api.types.is_numeric_dtype(df[c])
    ]

    first_numeric = num_cols[0] if len(num_cols) >= 1 else None
    second_numeric = num_cols[1] if len(num_cols) >= 2 else first_numeric
    first_grouping = str_cols[0] if str_cols else "entity_id"

    return {
        "histogram": {
            "value": first_numeric,
        },
        "bar-category": {
            "grouping": first_grouping,
        },
        "boxplot": {
            "value": first_numeric,
        },
        "scatter": {
            "value": first_numeric,
            "value_secondary": second_numeric,
        },
        "grouped-comparison": {
            "value": first_numeric,
            "grouping": first_grouping,
        },
    }


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
            detail="No dataset loaded. Select and run a dataset to view charts.",
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


def validate_sql_config(config):
    if not getattr(config, "sql_connection_string", None):
        logger.warning(
            "SQL connection string not configured",
            extra={
                "event": "startup_warning",
                "warning_type": "sql_not_configured",
                "warning_message": "SQL datasets will fail at runtime",
            },
        )
        return False
    else:
        logger.info(
            "SQL configuration detected",
            extra={
                "event": "startup_check",
                "sql_configured": True,
            },
        )
        return True


SQL_CONFIGURED = validate_sql_config(runtime_config)

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

if runtime_config.cors_allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(runtime_config.cors_allowed_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
        "sql_configured": SQL_CONFIGURED,
    }


@app.get("/charts/overview")
def charts_overview():
    config = StorageConfig()
    storage = LocalStorage(storage_path=config.storage_path)
    records = storage.load_records()

    if not records:
        raise HTTPException(
            status_code=422,
            detail="No dataset loaded. Select and run a dataset to view charts.",
        )

    session = get_session_state()
    active_dataset = session.get("active_dataset") or "unknown"
    source_metadata = session.get("dataset_source_metadata") or {
        "dataset_id": active_dataset,
        "source_type": None,
        "source_name": active_dataset,
        "source_url": None,
        "source_location": None,
    }

    rows = []
    for r in records:
        row = {"entity_id": r.get("entity_id", "")}
        row.update(r.get("features", {}))
        rows.append(row)

    df = pd.DataFrame(rows)

    total_rows = len(df)
    total_columns = len(df.columns)

    def _round_if_number(value):
        if pd.isna(value):
            return None
        if hasattr(value, "item"):
            value = value.item()
        if isinstance(value, (int, float)):
            return round(float(value), 4)
        return value

    num_cols = [
        c for c in df.columns
        if c != "entity_id" and pd.api.types.is_numeric_dtype(df[c])
    ]

    cat_cols = [
        c for c in df.columns
        if c != "entity_id" and not pd.api.types.is_numeric_dtype(df[c])
    ]

    missing_by_column = {
        str(col): int(df[col].isna().sum())
        for col in df.columns
    }

    numeric_summary = []
    for col in num_cols:
        col_name = str(col)
        series = df[col]
        non_null = series.dropna()
        numeric_summary.append(
            {
                "field": col_name,
                "count": int(non_null.count()),
                "missing": int(series.isna().sum()),
                "min": _round_if_number(non_null.min()) if len(non_null) > 0 else None,
                "max": _round_if_number(non_null.max()) if len(non_null) > 0 else None,
                "mean": _round_if_number(non_null.mean()) if len(non_null) > 0 else None,
                "median": _round_if_number(non_null.median()) if len(non_null) > 0 else None,
                "std": _round_if_number(non_null.std()) if len(non_null) > 1 else None,
            }
        )

    categorical_summary = []
    for col in cat_cols:
        col_name = str(col)
        series = df[col]
        non_null = series.dropna()
        value_counts = non_null.astype(str).value_counts().head(10)
        top_values = [
            {
                "value": str(value),
                "count": int(count),
            }
            for value, count in value_counts.items()
        ]
        categorical_summary.append(
            {
                "field": col_name,
                "count": int(non_null.count()),
                "missing": int(series.isna().sum()),
                "unique": int(non_null.nunique()),
                "top_values": top_values,
            }
        )

    stats: dict = {}
    if num_cols:
        first_numeric_col = num_cols[0]
        series = df[first_numeric_col].dropna()
        if len(series) > 0:
            stats = {
                "min": _round_if_number(series.min()),
                "max": _round_if_number(series.max()),
                "mean": _round_if_number(series.mean()),
                "count": int(len(series)),
            }

    chart_context = {
        chart_id: {
            role: str(field_name) if field_name is not None else None
            for role, field_name in fields.items()
        }
        for chart_id, fields in _build_chart_context(df).items()
    }

    return {
        "source": source_metadata.get("source_name") or active_dataset,
        "source_metadata": source_metadata,
        "rows": total_rows,
        "variables": total_columns,
        "shape": {
            "rows": total_rows,
            "columns": total_columns,
        },
        "fields": [str(col) for col in df.columns],
        "missing_by_column": missing_by_column,
        "numeric_summary": numeric_summary,
        "categorical_summary": categorical_summary,
        "chart_context": chart_context,
        **stats,
    }

