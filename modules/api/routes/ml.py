from typing import Any, Dict, List

from fastapi import APIRouter

from modules.ml.anomaly_isolation import IsolationForestModel
from modules.ml.anomaly_zscore import ZScoreAnomalyModel
from modules.ml.feature_pipeline import build_feature_dataset
from modules.ml.prediction_moving_average import MovingAverageModel
from modules.ml.prediction_regression import LinearRegressionModel
from modules.api.session_state import set_anomaly_status, set_prediction_status

router = APIRouter(prefix="/ml", tags=["ml"])


@router.post("/anomaly/zscore")
def run_zscore_anomaly(records: List[Dict[str, Any]]):
    set_anomaly_status("running")
    try:
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


@router.post("/anomaly/isolation-forest")
def run_isolation_forest(records: List[Dict[str, Any]]):
    set_anomaly_status("running")
    try:
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


@router.post("/prediction/regression")
def run_linear_regression(
    records: List[Dict[str, Any]],
    steps_ahead: int = 2,
):
    set_prediction_status("running")
    try:
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


@router.post("/prediction/moving-average")
def run_moving_average(
    records: List[Dict[str, Any]],
    steps_ahead: int = 2,
):
    set_prediction_status("running")
    try:
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
