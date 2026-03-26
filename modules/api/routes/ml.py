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


def _load_ml_records() -> list:
    """Load persisted canonical records and flatten them for ML consumption."""
    config = StorageConfig()
    storage = LocalStorage(storage_path=config.storage_path)
    records = storage.load_records()

    if not records:
        raise HTTPException(
            status_code=422,
            detail="No dataset loaded. Upload and run a dataset first.",
        )

    flat = []
    for i, r in enumerate(records):
        features = r.get("features", {})
        # Map the first numeric feature to ``value``
        value = None
        for v in features.values():
            try:
                value = float(v)
                break
            except (TypeError, ValueError):
                continue
        flat.append({
            "entity_id": str(r.get("entity_id", i)),
            "timestamp": str(r.get("timestamp", i)),
            "value": value,
        })

    return flat


@router.get("/anomaly/zscore")
def run_zscore_anomaly():
    set_anomaly_status("running")
    try:
        records = _load_ml_records()
        dataset = build_feature_dataset(records)

        model = ZScoreAnomalyModel(threshold=1.5)
        predictions = model.predict(dataset.records)
        summary = model.evaluate(dataset.records)
        set_anomaly_status("completed")

        return {
            "result": [p.model_dump() for p in predictions],
            "summary": summary.model_dump(),
        }
    except Exception:
        set_anomaly_status("idle")
        raise


@router.get("/anomaly/isolation-forest")
def run_isolation_forest():
    set_anomaly_status("running")
    try:
        records = _load_ml_records()
        dataset = build_feature_dataset(records)

        model = IsolationForestModel(contamination=0.1)
        predictions = model.predict(dataset.records)
        summary = model.evaluate(dataset.records)
        set_anomaly_status("completed")

        return {
            "result": [p.model_dump() for p in predictions],
            "summary": summary.model_dump(),
        }
    except Exception:
        set_anomaly_status("idle")
        raise


@router.get("/anomaly/kmeans")
def run_kmeans_anomaly():
    set_anomaly_status("running")
    try:
        records = _load_ml_records()
        dataset = build_feature_dataset(records)

        model = KMeansAnomalyModel(n_clusters=3)
        summary = model.evaluate(dataset.records)
        set_anomaly_status("completed")

        return {
            "status": "completed",
            "anomalies": summary.anomaly_count,
            "total": summary.total_records,
            "summary": summary.model_dump(),
            "notes": "K-Means clustering using distance from centroid.",
            "result": [p.model_dump() for p in summary.records],
        }
    except Exception:
        set_anomaly_status("idle")
        raise


@router.get("/prediction/regression")
def run_linear_regression(steps_ahead: int = 5):
    set_prediction_status("running")
    try:
        records = _load_ml_records()
        dataset = build_feature_dataset(records)

        model = LinearRegressionModel()
        predictions = model.predict(dataset.records, steps_ahead=steps_ahead)
        set_prediction_status("completed")

        return {
            "result": [p.model_dump() for p in predictions],
        }
    except Exception:
        set_prediction_status("idle")
        raise


@router.get("/prediction/moving-average")
def run_moving_average(steps_ahead: int = 5):
    set_prediction_status("running")
    try:
        records = _load_ml_records()
        dataset = build_feature_dataset(records)

        model = MovingAverageModel(window_size=2)
        predictions = model.predict(dataset.records, steps_ahead=steps_ahead)
        set_prediction_status("completed")

        return {
            "result": [p.model_dump() for p in predictions],
        }
    except Exception:
        set_prediction_status("idle")
        raise
