import math
from fastapi import APIRouter, HTTPException
from modules.ml.anomaly_kmeans import KMeansAnomalyModel
from modules.ml.anomaly_isolation import IsolationForestModel
from modules.ml.anomaly_zscore import ZScoreAnomalyModel
from modules.ml.feature_pipeline import build_feature_dataset
from modules.ml.prediction_moving_average import MovingAverageModel
from modules.ml.prediction_regression import LinearRegressionModel
from modules.api.session_state import set_anomaly_status, set_prediction_status
from modules.config.storage_config import StorageConfig
from modules.persistence.local_storage import LocalStorage

router = APIRouter(prefix="/ml", tags=["ml"])


def _is_valid_number(value) -> bool:
    """Check if value is a valid number (not None and not NaN)."""
    if value is None:
        return False
    try:
        float_val = float(value)
        return not math.isnan(float_val)
    except (TypeError, ValueError):
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
    """Clean records by removing rows with NaN values."""
    cleaned = []
    valid_values = []
    
    # First pass: collect all valid numeric values
    for record in records:
        value = record.get("value")
        if value is not None:
            try:
                float_val = float(value)
                if not math.isnan(float_val):
                    valid_values.append(record)
            except (TypeError, ValueError):
                pass
    
    return valid_values if valid_values else records


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
    """Load persisted canonical records and flatten them for model consumption."""
    config = StorageConfig()
    storage = LocalStorage(storage_path=config.storage_path)
    records = storage.load_records()

    if not records:
        raise HTTPException(
            status_code=422,
            detail="No dataset loaded. Select and run a dataset first.",
        )

    flat = []
    for i, r in enumerate(records):
        features = r.get("features", {})
        # Map the first numeric feature to ``value``
        value = None
        for v in features.values():
            if _is_valid_number(v):
                value = float(v)
                break
        flat.append({
            "row_id": i,
            "entity_id": str(r.get("entity_id", i)),
            "timestamp": str(r.get("timestamp", i)),
            "value": value,
            "features": features,
        })

    # Clean records to remove NaN values before model processing
    return _clean_records_for_ml(flat)


def _get_ml_dataset_context(records: list) -> dict:
    """Return role-based field context for ML endpoints."""
    value_field = "value" if records else None
    return {
        "identifier": "entity_id",
        "time": "timestamp",
        "value": value_field,
    }


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
        }
        return _sanitize_for_json(response)
    except Exception:
        set_anomaly_status("idle")
        raise


@router.get("/prediction/regression")
def run_linear_regression(steps_ahead: int = 5):
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
        }
        return _sanitize_for_json(response)
    except Exception:
        set_prediction_status("idle")
        raise


@router.get("/prediction/moving-average")
def run_moving_average(steps_ahead: int = 5):
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
        }
        return _sanitize_for_json(response)
    except Exception:
        set_prediction_status("idle")
        raise
