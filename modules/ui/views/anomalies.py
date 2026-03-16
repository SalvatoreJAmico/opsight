import json
from pathlib import Path

import pandas as pd
import streamlit as st


def render_anomalies_view():
    st.subheader("Anomaly Visualization")

    project_root = Path(__file__).resolve().parents[3]
    records_path = project_root / "data" / "records.json"

    if not records_path.exists():
        st.info("No processed records available yet.")
        return

    with open(records_path, "r") as f:
        records = json.load(f)

    if not records:
        st.info("No processed records available yet.")
        return

    flat_rows = []
    for record in records:
        row = {
            "entity_id": record.get("entity_id"),
            "timestamp": record.get("timestamp"),
            **record.get("features", {}),
        }
        flat_rows.append(row)

    df = pd.DataFrame(flat_rows)

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if not numeric_cols:
        st.info("No numeric features available for anomaly detection.")
        return

    feature = st.selectbox("Select numeric feature", numeric_cols)

    q1 = df[feature].quantile(0.25)
    q3 = df[feature].quantile(0.75)
    iqr = q3 - q1

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    df["is_anomaly"] = (df[feature] < lower) | (df[feature] > upper)

    st.write(f"Anomaly threshold for **{feature}**: < {lower:.2f} or > {upper:.2f}")
    st.metric("Anomalies Detected", int(df["is_anomaly"].sum()))

    st.write("### Feature Distribution")
    st.bar_chart(df[[feature]])

    st.write("### Records")
    st.dataframe(df, width="stretch")

    anomalies = df[df["is_anomaly"]]

    if anomalies.empty:
        st.success("No anomalies detected for the selected feature.")
    else:
        st.write("### Anomalous Records")
        st.dataframe(anomalies, width="stretch")