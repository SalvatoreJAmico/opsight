from typing import Any, Dict

import pandas as pd


def evaluate(scored_records: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate evaluation metrics from scored anomaly records.

    Expected input:
    DataFrame with at least:
    - anomaly_score
    - is_anomaly
    - severity

    Returns:
    dict with summary metrics for reporting, API, or dashboard use.
    """
    if scored_records.empty:
        return {
            "total_records": 0,
            "anomaly_count": 0,
            "anomaly_rate": 0.0,
            "severity_breakdown": {},
            "score_distribution": {},
        }

    df = scored_records.copy()

    if "is_anomaly" not in df.columns:
        df["is_anomaly"] = False

    if "anomaly_score" not in df.columns:
        df["anomaly_score"] = 0.0

    if "severity" not in df.columns:
        df["severity"] = "low"

    total_records = len(df)
    anomaly_count = int(df["is_anomaly"].sum())
    anomaly_rate = anomaly_count / total_records if total_records > 0 else 0.0

    severity_breakdown = {
        str(k): int(v) for k, v in df["severity"].value_counts().to_dict().items()
    }

    score_distribution = {
        str(k): int(v) for k, v in df["anomaly_score"].value_counts().sort_index().to_dict().items()
    }

    return {
        "total_records": total_records,
        "anomaly_count": anomaly_count,
        "anomaly_rate": anomaly_rate,
        "severity_breakdown": severity_breakdown,
        "score_distribution": score_distribution,
    }