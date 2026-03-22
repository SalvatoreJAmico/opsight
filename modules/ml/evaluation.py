from typing import List

from modules.ml.schemas import FeatureRecord, PredictionRecord

import math
from sklearn.metrics import roc_auc_score

def evaluate_prediction_regression(
    records: List[FeatureRecord],
    predictions: List[PredictionRecord],
) -> dict:
    y_true = []
    y_pred = []

    for record, prediction in zip(records, predictions):
        if record.value is None or prediction.value is None:
            continue

        y_true.append(float(record.value))
        y_pred.append(float(prediction.value))

    if not y_true:
        return {
            "mae": None,
            "mse": None,
            "rmse": None,
            "r2": None,
            "support": 0,
        }

    n = len(y_true)

    mae = sum(abs(yt - yp) for yt, yp in zip(y_true, y_pred)) / n
    mse = sum((yt - yp) ** 2 for yt, yp in zip(y_true, y_pred)) / n
    rmse = math.sqrt(mse)

    mean_true = sum(y_true) / n
    ss_tot = sum((yt - mean_true) ** 2 for yt in y_true)
    ss_res = sum((yt - yp) ** 2 for yt, yp in zip(y_true, y_pred))
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    return {
        "mae": round(mae, 4),
        "mse": round(mse, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4),
        "support": n,
    }
def evaluate_anomaly_classification(
    records: List[FeatureRecord],
    predictions: List[PredictionRecord],
) -> dict:
    y_true = []
    y_pred = []

    for record, prediction in zip(records, predictions):
        if record.label is None:
            continue

        y_true.append(int(record.label))
        y_pred.append(1 if prediction.is_anomaly else 0)

    if not y_true:
        return {
            "precision": None,
            "recall": None,
            "f1_score": None,
            "support": 0,
            "true_positives": 0,
            "false_positives": 0,
            "true_negatives": 0,
            "false_negatives": 0,
        }

    tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 1)
    fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 1)
    tn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 0)
    fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 0)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1_score = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1_score, 4),
        "support": len(y_true),
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
    }

def compare_anomaly_models(results: dict) -> dict:
    return {
        "model_type": "anomaly",
        "models": results,
    }


def compare_prediction_models(results: dict) -> dict:
    return {
        "model_type": "prediction",
        "models": results,
    }

def evaluate_anomaly_roc_auc(
    records: List[FeatureRecord],
    predictions: List[PredictionRecord],
) -> dict:
    y_true = []
    y_score = []

    for record, prediction in zip(records, predictions):
        if record.label is None or prediction.anomaly_score is None:
            continue

        y_true.append(int(record.label))
        y_score.append(float(prediction.anomaly_score))

    if len(set(y_true)) < 2:
        return {
            "roc_auc": None,
            "support": len(y_true),
        }

    try:
        score = roc_auc_score(y_true, y_score)
        return {
            "roc_auc": round(float(score), 4),
            "support": len(y_true),
        }
    except ValueError:
        return {
            "roc_auc": None,
            "support": len(y_true),
        }