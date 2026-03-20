import requests
import streamlit as st

from modules.streamlit_ui.views._config import API_BASE_URL


def render_metrics_view():
    st.subheader("Pipeline Metrics Dashboard")

    try:
        response = requests.get(f"{API_BASE_URL}/pipeline/status")

        if response.status_code != 200:
            st.error("Failed to load pipeline metrics")
            return

        summary = response.json()

        if summary.get("status") == "no runs recorded":
            st.info("No pipeline runs recorded yet.")
            return

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Records Ingested", summary.get("records_ingested", 0))
        col2.metric("Valid Records", summary.get("records_valid", 0))
        col3.metric("Invalid Records", summary.get("records_invalid", 0))
        col4.metric("Persisted Records", summary.get("records_persisted", 0))

        st.write("### Validation Breakdown")
        st.bar_chart({
            "count": [
                summary.get("records_valid", 0),
                summary.get("records_invalid", 0),
            ]
        })

        st.write("### Run Summary")
        st.json(summary)

    except Exception as exc:
        st.error(f"Failed to connect to API: {exc}")