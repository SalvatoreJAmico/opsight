import logging
import time
import pandas as pd
from pathlib import Path
from collections import Counter

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware

from modules.config.logging_config import setup_logging
from modules.config.runtime_config import load_runtime_config
from modules.api.session_state import reset_session_state
from modules.api.session_state import get_session_state
from modules.api.session_state import set_selected_variables
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
from modules.ingestion.ingestion import ingest_data
from modules.adapter.adapter import adapt_records
from modules.validation.validator import validate_canonical_record
from modules.validation.duplicate_check import detect_duplicates


ASSIGNMENT_TARGET_VARIABLE = "Sales"
ASSIGNMENT_COMPARE_VARIABLES = ["Profit", "Quantity", "Discount", "Category", "Order Date"]
ASSIGNMENT_ANALYSIS_FIELDS = [ASSIGNMENT_TARGET_VARIABLE, *ASSIGNMENT_COMPARE_VARIABLES]
ASSIGNMENT_FIELD_CANDIDATES = {
    "Sales": ("sales",),
    "Profit": ("profit",),
    "Quantity": ("quantity",),
    "Discount": ("discount",),
    "Category": ("category",),
    "Order Date": ("order date", "order_date", "timestamp"),
}


def _normalize_field_name(field_name) -> str:
    return str(field_name).strip().lower().replace("_", " ")


def _resolve_assignment_column(df: pd.DataFrame, label: str):
    normalized_columns = {
        _normalize_field_name(column): column
        for column in df.columns
    }

    for candidate in ASSIGNMENT_FIELD_CANDIDATES[label]:
        matched_column = normalized_columns.get(_normalize_field_name(candidate))
        if matched_column is not None:
            return matched_column

    return None


def _resolve_assignment_fields(df: pd.DataFrame) -> dict:
    return {
        label: column
        for label in ASSIGNMENT_ANALYSIS_FIELDS
        for column in [_resolve_assignment_column(df, label)]
        if column is not None
    }


def _get_assignment_series(df: pd.DataFrame, column_name, label: str) -> pd.Series:
    series = df[column_name]
    if label == "Order Date":
        return pd.to_datetime(series, errors="coerce")
    return series


def _validate_target_variable(target_variable: str) -> str:
    if target_variable != ASSIGNMENT_TARGET_VARIABLE:
        raise HTTPException(
            status_code=422,
            detail=f"Target variable must be '{ASSIGNMENT_TARGET_VARIABLE}'.",
        )

    return target_variable


def _validate_compare_variable(compare_variable: str) -> str:
    if compare_variable not in ASSIGNMENT_COMPARE_VARIABLES:
        raise HTTPException(
            status_code=422,
            detail=(
                "Compare variable must be one of "
                f"{', '.join(ASSIGNMENT_COMPARE_VARIABLES)}."
            ),
        )

    return compare_variable


def _resolve_chart_columns(
    df: pd.DataFrame,
    *,
    target_variable: str = ASSIGNMENT_TARGET_VARIABLE,
    compare_variable: str | None = None,
):
    resolved_fields = _resolve_assignment_fields(df)
    target_label = _validate_target_variable(target_variable)
    target_column = resolved_fields.get(target_label)

    if target_column is None:
        raise HTTPException(
            status_code=422,
            detail=f"Target variable '{target_label}' is not available in the active dataset.",
        )

    compare_label = None
    compare_column = None
    if compare_variable is not None:
        compare_label = _validate_compare_variable(compare_variable)
        compare_column = resolved_fields.get(compare_label)
        if compare_column is None:
            raise HTTPException(
                status_code=422,
                detail=f"Compare variable '{compare_label}' is not available in the active dataset.",
            )

    return target_column, compare_column, resolved_fields, target_label, compare_label


def _records_to_chart_df(records: list) -> pd.DataFrame:
    """Flatten canonical records into a chart-ready DataFrame."""
    rows = []
    for r in records:
        row = {
            "entity_id": r.get("entity_id", ""),
            "timestamp": r.get("timestamp"),
        }
        row.update(r.get("features", {}))
        rows.append(row)

    return pd.DataFrame(rows)


def _infer_data_format(source_path: str | None, source_type: str | None) -> str | None:
    if source_type == "sql" or (source_path and str(source_path).startswith("sql://")):
        return "sql"

    suffix = Path(str(source_path or "")).suffix.lower()
    if suffix in {".csv", ".json", ".parquet", ".xlsx", ".xls"}:
        return suffix.lstrip(".")

    return None


def _flatten_canonical_records(records: list[dict]) -> pd.DataFrame:
    rows = []
    for record in records:
        row = {
            "entity_id": record.get("entity_id", ""),
            "timestamp": record.get("timestamp"),
        }
        row.update(record.get("features", {}))
        rows.append(row)
    return pd.DataFrame(rows)


def _missing_counts(records: list[dict]) -> dict:
    if not records:
        return {}

    dataframe = _flatten_canonical_records(records)
    if dataframe.empty:
        return {}

    return {
        str(column): int(dataframe[column].isna().sum())
        for column in dataframe.columns
    }


def _build_chart_context(df: pd.DataFrame, compare_variable: str = "Profit") -> dict:
    """Return per-chart field-role context from the active dataset."""
    resolved_fields = _resolve_assignment_fields(df)
    compare_label = compare_variable if compare_variable in resolved_fields else None
    if compare_label is None:
        compare_label = next(
            (label for label in ASSIGNMENT_COMPARE_VARIABLES if label in resolved_fields),
            None,
        )
    target_label = ASSIGNMENT_TARGET_VARIABLE if ASSIGNMENT_TARGET_VARIABLE in resolved_fields else None

    return {
        "histogram": {
            "target_variable": target_label,
        },
        "bar-category": {
            "compare_variable": compare_label,
        },
        "boxplot": {
            "target_variable": target_label,
        },
        "scatter": {
            "target_variable": target_label,
            "compare_variable": compare_label,
        },
        "grouped-comparison": {
            "target_variable": target_label,
            "compare_variable": compare_label,
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
def histogram(target_variable: str = ASSIGNMENT_TARGET_VARIABLE):
    try:
        df = get_chart_dataframe()
        target_column, _, _, target_label, _ = _resolve_chart_columns(
            df,
            target_variable=target_variable,
        )
        path = create_histogram(df, target_column=target_column, target_label=target_label)
        return {"image": path}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Histogram generation failed: {str(exc)}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/charts/bar-category")
def bar_category(
    target_variable: str = ASSIGNMENT_TARGET_VARIABLE,
    compare_variable: str = "Category",
):
    try:
        df = get_chart_dataframe()
        _, compare_column, _, _, compare_label = _resolve_chart_columns(
            df,
            target_variable=target_variable,
            compare_variable=compare_variable,
        )
        path = create_bar_category_chart(
            df,
            compare_column=compare_column,
            compare_label=compare_label,
        )
        return {"image": path}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Bar chart generation failed: {str(exc)}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/charts/boxplot")
def boxplot(target_variable: str = ASSIGNMENT_TARGET_VARIABLE):
    try:
        df = get_chart_dataframe()
        target_column, _, _, target_label, _ = _resolve_chart_columns(
            df,
            target_variable=target_variable,
        )
        path = create_boxplot(df, target_column=target_column, target_label=target_label)
        return {"image": path}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Box plot generation failed: {str(exc)}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/charts/scatter")
def scatter(
    target_variable: str = ASSIGNMENT_TARGET_VARIABLE,
    compare_variable: str = "Profit",
):
    try:
        df = get_chart_dataframe()
        target_column, compare_column, _, target_label, compare_label = _resolve_chart_columns(
            df,
            target_variable=target_variable,
            compare_variable=compare_variable,
        )
        path = create_scatter_plot(
            df,
            target_column=target_column,
            compare_column=compare_column,
            target_label=target_label,
            compare_label=compare_label,
        )
        return {"image": path}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Scatter plot generation failed: {str(exc)}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/charts/grouped-comparison")
def grouped_comparison(
    target_variable: str = ASSIGNMENT_TARGET_VARIABLE,
    compare_variable: str = "Category",
):
    try:
        df = get_chart_dataframe()
        target_column, compare_column, _, target_label, compare_label = _resolve_chart_columns(
            df,
            target_variable=target_variable,
            compare_variable=compare_variable,
        )
        path = create_grouped_comparison_chart(
            df,
            target_column=target_column,
            compare_column=compare_column,
            target_label=target_label,
            compare_label=compare_label,
        )
        return {"image": path}
    except HTTPException:
        raise
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
        row = {
            "entity_id": r.get("entity_id", ""),
            "timestamp": r.get("timestamp"),
        }
        row.update(r.get("features", {}))
        rows.append(row)

    df = pd.DataFrame(rows)

    total_rows = len(df)
    total_columns = len(df.columns)
    resolved_fields = _resolve_assignment_fields(df)
    analysis_fields = list(resolved_fields.keys())

    def _round_if_number(value):
        if pd.isna(value):
            return None
        if hasattr(value, "item"):
            value = value.item()
        if isinstance(value, (int, float)):
            return round(float(value), 4)
        return value

    missing_by_column = {
        label: int(_get_assignment_series(df, column, label).isna().sum())
        for label, column in resolved_fields.items()
    }

    numeric_summary = []
    for label in ["Sales", "Profit", "Quantity", "Discount"]:
        column = resolved_fields.get(label)
        if column is None:
            continue
        series = _get_assignment_series(df, column, label)
        non_null = series.dropna()
        numeric_summary.append(
            {
                "field": label,
                "count": int(non_null.count()),
                "missing": int(series.isna().sum()),
                "min": _round_if_number(non_null.min()) if len(non_null) > 0 else None,
                "max": _round_if_number(non_null.max()) if len(non_null) > 0 else None,
                "mean": _round_if_number(non_null.mean()) if len(non_null) > 0 else None,
                "median": _round_if_number(non_null.median()) if len(non_null) > 0 else None,
                "std": _round_if_number(non_null.std()) if len(non_null) > 1 else None,
            }
        )

    date_summary = []
    for label in ["Order Date"]:
        column = resolved_fields.get(label)
        if column is None:
            continue
        series = _get_assignment_series(df, column, label)
        non_null = series.dropna()
        date_summary.append(
            {
                "field": label,
                "count": int(non_null.count()),
                "missing": int(series.isna().sum()),
                "min_date": str(non_null.min().date()) if len(non_null) > 0 else None,
                "max_date": str(non_null.max().date()) if len(non_null) > 0 else None,
            }
        )

    categorical_summary = []
    for label in ["Category"]:
        column = resolved_fields.get(label)
        if column is None:
            continue
        series = _get_assignment_series(df, column, label)
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
                "field": label,
                "count": int(non_null.count()),
                "missing": int(series.isna().sum()),
                "unique": int(non_null.nunique()),
                "top_values": top_values,
            }
        )

    stats: dict = {}
    sales_column = resolved_fields.get(ASSIGNMENT_TARGET_VARIABLE)
    if sales_column is not None:
        series = _get_assignment_series(df, sales_column, ASSIGNMENT_TARGET_VARIABLE).dropna()
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
        "variables": len(analysis_fields),
        "shape": {
            "rows": total_rows,
            "columns": total_columns,
        },
        "fields": analysis_fields,
        "missing_by_column": missing_by_column,
        "numeric_summary": numeric_summary,
        "date_summary": date_summary,
        "categorical_summary": categorical_summary,
        "chart_context": chart_context,
        "assignment_analysis": {
            "target_variable": ASSIGNMENT_TARGET_VARIABLE,
            "target_options": [ASSIGNMENT_TARGET_VARIABLE],
            "compare_options": [
                label for label in ASSIGNMENT_COMPARE_VARIABLES
                if label in resolved_fields
            ],
        },
        **stats,
    }


@app.get("/cleaning/audit")
def cleaning_audit_overview():
    config = StorageConfig()
    storage = LocalStorage(storage_path=config.storage_path)
    cleaned_records = storage.load_records()

    if not cleaned_records:
        raise HTTPException(
            status_code=422,
            detail="No dataset loaded. Select and run a dataset to view the cleaning audit.",
        )

    session = get_session_state()
    source_metadata = session.get("dataset_source_metadata") or {}
    source_path = source_metadata.get("source_location")
    source_type = source_metadata.get("source_type")

    if not source_path:
        raise HTTPException(
            status_code=422,
            detail="Dataset source metadata is unavailable. Re-run the dataset to generate a cleaning audit.",
        )

    source_format = _infer_data_format(source_path, source_type)

    try:
        raw_dataframe = ingest_data(source_path=source_path, source_mode=None, data_format=source_format)
        canonical_records = adapt_records(raw_dataframe)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to build cleaning audit from source data: {exc}",
        ) from exc

    invalid_reason_counter = Counter()
    valid_records = []
    invalid_records = []

    for record in canonical_records:
        validation_result = validate_canonical_record(record)
        if validation_result.get("status") == "valid":
            valid_records.append(record)
        else:
            invalid_records.append(record)
            for error in validation_result.get("errors", []):
                invalid_reason_counter[str(error)] += 1

    duplicate_before = detect_duplicates(canonical_records)
    duplicate_after = detect_duplicates(cleaned_records)

    return {
        "source": {
            "dataset_id": source_metadata.get("dataset_id"),
            "source_name": source_metadata.get("source_name"),
            "source_type": source_type,
            "source_location": source_path,
        },
        "row_counts": {
            "before": len(canonical_records),
            "after": len(cleaned_records),
        },
        "missing_by_column": {
            "before": _missing_counts(canonical_records),
            "after": _missing_counts(cleaned_records),
        },
        "duplicates": {
            "before": len(duplicate_before.get("duplicate_records", [])),
            "after": len(duplicate_after.get("duplicate_records", [])),
        },
        "invalid_rows_removed": {
            "count": len(invalid_records),
            "reason_counts": dict(invalid_reason_counter),
        },
        "records_valid_before_cleaning": len(valid_records),
    }


@app.get("/variables/selection")
def get_variable_selection():
    state = get_session_state()
    return state.get("selected_variables", {"target": None, "compare": []})


@app.post("/variables/selection")
async def save_variable_selection(request: Request):
    body = await request.json()
    target = body.get("target")
    compare = body.get("compare", [])

    if target is not None and not isinstance(target, str):
        raise HTTPException(status_code=422, detail="target must be a string or null")
    if not isinstance(compare, list):
        raise HTTPException(status_code=422, detail="compare must be a list")
    if not all(isinstance(v, str) for v in compare):
        raise HTTPException(status_code=422, detail="each compare value must be a string")

    set_selected_variables(target, compare)
    return get_session_state()["selected_variables"]
