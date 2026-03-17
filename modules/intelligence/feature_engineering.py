from typing import Any, Dict, List

import pandas as pd


def build_features(records: List[Dict[str, Any]], normalize: bool = False) -> pd.DataFrame:
    """
    Convert canonical records into an analysis-ready feature DataFrame.

    Expected canonical record structure:
        {
            "entity_id": ...,
            "timestamp": ...,
            "features": {...},
            "metadata": {...}
        }

    Returns a DataFrame containing:
    - entity_id
    - timestamp
    - flattened feature columns
    - optional derived metrics
    """
    if not isinstance(records, list):
        raise ValueError("records must be a list")

    if not records:
        return pd.DataFrame()

    rows = []
    for record in records:
        if not isinstance(record, dict):
            continue

        row = {
            "entity_id": record.get("entity_id"),
            "timestamp": record.get("timestamp"),
        }

        features = record.get("features", {})
        if isinstance(features, dict):
            row.update(features)

        rows.append(row)

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    # Optional simple derived metrics
    if numeric_cols:
        df["feature_count"] = df[numeric_cols].notna().sum(axis=1)
        df["feature_sum"] = df[numeric_cols].sum(axis=1)

    if normalize and numeric_cols:
        for col in numeric_cols:
            col_min = df[col].min()
            col_max = df[col].max()

            if pd.isna(col_min) or pd.isna(col_max):
                continue

            if col_max == col_min:
                df[col] = 0.0
            else:
                df[col] = (df[col] - col_min) / (col_max - col_min)

    return df