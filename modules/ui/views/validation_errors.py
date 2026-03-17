import requests
import streamlit as st
import pandas as pd

from modules.ui.views._config import API_BASE_URL


def render_validation_errors():
    st.subheader("Validation Error Visualization")

    try:
        response = requests.get(f"{API_BASE_URL}/pipeline/status")

        if response.status_code != 200:
            st.error("Could not load pipeline status")
            return

        summary = response.json()

        invalid_count = summary.get("records_invalid", 0)

        if invalid_count == 0:
            st.success("No validation errors detected in the latest pipeline run.")
            return

        st.metric("Invalid Records", invalid_count)

        error_data = {
            "error_type": ["invalid_records"],
            "count": [invalid_count],
        }

        df = pd.DataFrame(error_data)

        st.write("### Error Breakdown")
        st.bar_chart(df.set_index("error_type"))

        st.write("### Pipeline Summary")
        st.json(summary)

    except Exception as exc:
        st.error(f"Failed to connect to API: {exc}")