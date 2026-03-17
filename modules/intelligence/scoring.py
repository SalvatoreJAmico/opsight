from typing import Dict
import pandas as pd

LOW_THRESHOLD = 1.0
MEDIUM_THRESHOLD = 2.0
HIGH_THRESHOLD = 3.0


def score_records(anomaly_results: pd.DataFrame, thresholds: Dict[str, float] | None = None) -> pd.DataFrame:
    if anomaly_results.empty:
        return anomaly_results

    df = anomaly_results.copy()

    if "anomaly_score" not in df.columns:
        df["anomaly_score"] = 0.0

    if "is_anomaly" not in df.columns:
        df["is_anomaly"] = False

    config = thresholds or {
        "low": LOW_THRESHOLD,
        "medium": MEDIUM_THRESHOLD,
        "high": HIGH_THRESHOLD,
    }

    def get_severity(score: float) -> str:
        if score >= config["high"]:
            return "critical"
        if score >= config["medium"]:
            return "high"
        if score >= config["low"]:
            return "medium"
        return "low"

    df["severity"] = df["anomaly_score"].apply(get_severity)
    df["alert"] = df["is_anomaly"].apply(lambda x: "ALERT" if x else "OK")

    return df