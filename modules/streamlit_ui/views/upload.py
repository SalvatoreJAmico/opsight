import requests
import streamlit as st
from pathlib import Path

from modules.streamlit_ui.views._config import API_BASE_URL


def render_upload_view():
    st.subheader("Dataset Upload")
    access_code = st.text_input("Upload Access Code", type="password")

    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

    if uploaded_file is None:
        return

    data_dir = Path(__file__).resolve().parents[3] / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    saved_path = data_dir / uploaded_file.name

    with open(saved_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"File saved: {saved_path.name}")

    if st.button("Run Pipeline"):
        if not access_code:
            st.error("Upload access code is required to run the pipeline")
            return

        try:
            response = requests.post(
                f"{API_BASE_URL}/data",
                json={
                    "source_path": str(saved_path.resolve()),
                    "access_code": access_code,
                },
                headers={"X-Upload-Access-Code": access_code},
            )

            if response.status_code == 200:
                st.success("Pipeline executed successfully")
                st.json(response.json())
            else:
                st.error("Pipeline execution failed")
                st.json(response.json())

        except Exception as exc:
            st.error(f"API request failed: {exc}")