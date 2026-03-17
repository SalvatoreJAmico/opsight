from typing import Any, Dict, List

import pandas as pd
from modules.intelligence.feature_engineering import build_features


def detect_anomalies(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Detect anomalies using IQR method on numeric features.
    Returns DataFrame with anomaly flags.
    """
    df = build_features(records)

    if df.empty:
        return df

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if not numeric_cols:
        return df

    # initialize
    df["is_anomaly"] = False
    df["anomaly_score"] = 0.0

    for col in numeric_cols:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1

        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        mask = (df[col] < lower) | (df[col] > upper)

        df.loc[mask, "is_anomaly"] = True
        df.loc[mask, "anomaly_score"] += 1

    return df