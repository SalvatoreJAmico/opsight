import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from modules.ui.views.upload import render_upload_view
from modules.ui.views.metrics import render_metrics_view
from modules.ui.views.entity_explorer import render_entity_explorer
from modules.ui.views.validation_errors import render_validation_errors
from modules.ui.views.anomalies import render_anomalies_view
from modules.ui.views._config import PIPELINE_SUMMARY_PATH, STORAGE_PATH


st.set_page_config(page_title="Opsight UI", layout="wide")

st.title("Opsight Dashboard")
st.write("Phase 6 visualization service is running.")

records_path = Path(STORAGE_PATH)
summary_path = Path(PIPELINE_SUMMARY_PATH)

st.subheader("Connectivity Check")

st.write(f"Records file exists: {records_path.exists()}")
st.write(f"Pipeline summary exists: {summary_path.exists()}")

st.info("Placeholder UI loaded successfully. Dashboard views will be added next.")

render_upload_view()
render_metrics_view()
render_entity_explorer()
render_validation_errors()
render_anomalies_view()
