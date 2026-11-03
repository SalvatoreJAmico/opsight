import math
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from modules.api.chart_schema import schema_for
from modules.ml.anomaly_kmeans import KMeansAnomalyModel
from modules.ml.anomaly_isolation import IsolationForestModel
from modules.ml.anomaly_zscore import ZScoreAnomalyModel
from modules.ml.feature_pipeline import build_feature_dataset
from modules.ml.prediction_moving_average import MovingAverageModel
from modules.ml.prediction_regression import LinearRegressionModel
from modules.api.session_state import get_session_state, set_anomaly_status, set_prediction_status
from modules.config.storage_config import StorageConfig
from modules.persistence.local_storage import LocalStorage

router = APIRouter(prefix="/ml", tags=["ml"])


def _is_valid_number(value) -> bool:
    """Only finite measurements are usable; booleans are not measurements."""
    if value is None or isinstance(value, bool):
        return False
    try:
        float_val = float(value)
        return math.isfinite(float_val)
    except (TypeError, ValueError, OverflowError):
        return False


def _sanitize_for_json(obj):
    """Remove NaN and Infinity values from objects before JSON serialization."""
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_for_json(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    else:
        return obj


def _clean_records_for_ml(records: list) -> list:
    """Drop missing/nonfinite measurements without substituting another field."""
    return [record for record in records if _is_valid_number(record.get("value"))]


def _extract_key_feature_values(features: dict) -> dict:
    """Extract report-friendly key feature values from a record's feature map."""
    feature_lookup = {str(k).lower(): v for k, v in (features or {}).items()}
    return {
        "Sales": feature_lookup.get("sales"),
        "Profit": feature_lookup.get("profit"),
        "Discount": feature_lookup.get("discount"),
    }


def _build_isolation_forest_anomaly_sample(records: list, predictions: list, limit: int = 10) -> list:
    """Return a top-N sample of anomalous rows sorted by most anomalous score."""
    sample = []

    for record, prediction in zip(records, predictions):
        if not prediction.is_anomaly:
            continue

        key_values = _extract_key_feature_values(record.get("features", {}))
        sample.append(
            {
                "row_id": record.get("row_id", prediction.entity_id),
                "target_field": record.get("value_field", "value"),
                "target_value": prediction.value,
                "Sales": key_values.get("Sales"),
                "Profit": key_values.get("Profit"),
                "Discount": key_values.get("Discount"),
                "anomaly_score": prediction.anomaly_score,
            }
        )

    # Lower decision_function scores indicate stronger anomalies.
    sample.sort(
        key=lambda row: (
            row["anomaly_score"] is None,
            row["anomaly_score"] if row["anomaly_score"] is not None else float("inf"),
        )
    )
    return sample[:limit]


def _load_ml_records() -> list:
    """Load one selected numeric field consistently across all persisted rows."""
    state = get_session_state()
    status = state.get("pipeline_status")
    if status in {"running", "failed"} or (state.get("active_dataset") and status != "completed"):
        raise HTTPException(
            status_code=422,
            detail="The selected dataset has not completed processing. Run it successfully before running models.",
        )

    config = StorageConfig()
    storage = LocalStorage(storage_path=config.storage_path)
    records = storage.load_records()
    if not records:
        raise HTTPException(status_code=422, detail="No dataset loaded. Select and run a dataset first.")

    features_df = pd.DataFrame([record.get("features") or {} for record in records])
    fields, types = schema_for(features_df)
    choices = [label for label, column in fields.items()
               if types[label] == "numeric" and any(_is_valid_number(value) for value in features_df[column])]
    target = (state.get("selected_variables") or {}).get("target")
    if target:
        if target not in fields:
            raise HTTPException(status_code=422, detail=f"Target variable '{target}' is not available. Choose a numeric target in Charts.")
        if target not in choices:
            raise HTTPException(status_code=422, detail=f"Target variable '{target}' has no usable finite numeric values. Choose a numeric target in Charts.")
    elif "Sales" in choices:
        # Match the established sales-dashboard default, and report the real field.
        target = "Sales"
    elif len(choices) == 1:
        target = choices[0]
    elif not choices:
        raise HTTPException(status_code=422, detail="No usable finite numeric values are available for analysis.")
    else:
        raise HTTPException(status_code=422, detail="Choose a numeric target in Charts before running a model. Available fields: " + ", ".join(choices))

    column = fields[target]
    flat = []
    for i, record in enumerate(records):
        features = record.get("features") or {}
        value = features.get(column)
        if not _is_valid_number(value):
            continue
        flat.append({
            "row_id": i,
            "entity_id": str(record.get("entity_id", i)),
            "timestamp": str(record.get("timestamp", "")),
            "value": float(value),
            "features": features,
            "value_field": target,
            "input_records": len(records),
        })
    if not flat:
        raise HTTPException(status_code=422, detail="No usable finite numeric values are available for analysis.")
    return flat


def _get_ml_dataset_context(records: list) -> dict:
    """Return the actual selected field rather than a misleading generic value."""
    return {
        "identifier": "entity_id",
        "time": "timestamp",
        "value": records[0].get("value_field", "value") if records else None,
    }


def _get_data_quality(records: list) -> dict:
    total = records[0].get("input_records", len(records)) if records else 0
    return {"input_records": total, "usable_records": len(records), "excluded_records": total - len(records)}


@router.get("/anomaly/zscore")
def run_zscore_anomaly():
    set_anomaly_status("running")
    try:
        records = _load_ml_records()
        dataset_context = _get_ml_dataset_context(records)
        dataset = build_feature_dataset(records)

        model = ZScoreAnomalyModel(threshold=1.5)
        predictions = model.predict(dataset.records)
        summary = model.evaluate(dataset.records)
        set_anomaly_status("completed")

        response = {
            "result": [p.model_dump() for p in predictions],
            "summary": summary.model_dump(),
            "dataset_context": dataset_context,
            "data_quality": _get_data_quality(records),
        }
        return _sanitize_for_json(response)
    except Exception:
        set_anomaly_status("idle")
        raise


@router.get("/anomaly/isolation-forest")
def run_isolation_forest():
    set_anomaly_status("running")
    try:
        records = _load_ml_records()
        dataset_context = _get_ml_dataset_context(records)
        dataset = build_feature_dataset(records)

        model = IsolationForestModel(contamination=0.1)
        predictions = model.predict(dataset.records)
        summary = model.evaluate(dataset.records)
        anomaly_sample_top10 = _build_isolation_forest_anomaly_sample(records, predictions, limit=10)
        set_anomaly_status("completed")

        response = {
            "result": [p.model_dump() for p in predictions],
            "summary": summary.model_dump(),
            "anomaly_sample_top10": anomaly_sample_top10,
            "dataset_context": dataset_context,
            "data_quality": _get_data_quality(records),
        }
        return _sanitize_for_json(response)
    except Exception:
        set_anomaly_status("idle")
        raise


@router.get("/anomaly/kmeans")
def run_kmeans_anomaly():
    set_anomaly_status("running")
    try:
        records = _load_ml_records()
        dataset_context = _get_ml_dataset_context(records)
        dataset = build_feature_dataset(records)

        model = KMeansAnomalyModel(n_clusters=3)
        summary = model.evaluate(dataset.records)
        set_anomaly_status("completed")

        response = {
            "status": "completed",
            "anomalies": summary.anomaly_count,
            "total": summary.total_records,
            "summary": summary.model_dump(),
            "notes": "K-Means clustering using distance from centroid.",
            "result": [p.model_dump() for p in summary.records],
            "dataset_context": dataset_context,
            "data_quality": _get_data_quality(records),
        }
        return _sanitize_for_json(response)
    except Exception:
        set_anomaly_status("idle")
        raise


@router.get("/prediction/regression")
def run_linear_regression(steps_ahead: int = Query(default=5, ge=1, le=365)):
    set_prediction_status("running")
    try:
        records = _load_ml_records()
        dataset_context = _get_ml_dataset_context(records)
        dataset = build_feature_dataset(records)

        model = LinearRegressionModel()
        predictions = model.predict(dataset.records, steps_ahead=steps_ahead)
        set_prediction_status("completed")

        response = {
            "result": [p.model_dump() for p in predictions],
            "dataset_context": dataset_context,
            "data_quality": _get_data_quality(records),
        }
        return _sanitize_for_json(response)
    except ValueError as exc:
        set_prediction_status("idle")
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception:
        set_prediction_status("idle")
        raise


@router.get("/prediction/moving-average")
def run_moving_average(steps_ahead: int = Query(default=5, ge=1, le=365)):
    set_prediction_status("running")
    try:
        records = _load_ml_records()
        dataset_context = _get_ml_dataset_context(records)
        dataset = build_feature_dataset(records)

        model = MovingAverageModel(window_size=2)
        predictions = model.predict(dataset.records, steps_ahead=steps_ahead)
        set_prediction_status("completed")

        response = {
            "result": [p.model_dump() for p in predictions],
            "dataset_context": dataset_context,
            "data_quality": _get_data_quality(records),
        }
        return _sanitize_for_json(response)
    except ValueError as exc:
        set_prediction_status("idle")
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception:
        set_prediction_status("idle")
        raise
