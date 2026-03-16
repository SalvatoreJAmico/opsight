import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from modules.ui.views.upload import render_upload_view


st.set_page_config(page_title="Opsight UI", layout="wide")

st.title("Opsight Dashboard")
st.write("Phase 6 visualization service is running.")

project_root = Path(__file__).resolve().parents[2]
records_path = project_root / "data" / "records.json"
summary_path = project_root / "reports" / "pipeline_run_summary.json"

st.subheader("Connectivity Check")

st.write(f"Records file exists: {records_path.exists()}")
st.write(f"Pipeline summary exists: {summary_path.exists()}")

st.info("Placeholder UI loaded successfully. Dashboard views will be added next.")

render_upload_view()