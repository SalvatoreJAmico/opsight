import requests
import streamlit as st
import pandas as pd


def render_entity_explorer():
    st.subheader("Entity Record Explorer")

    entity_id = st.text_input("Enter entity_id")

    if not entity_id:
        return

    try:
        response = requests.get(f"http://127.0.0.1:8000/entity/{entity_id}")

        if response.status_code == 404:
            st.info("No records found for that entity_id.")
            return

        if response.status_code != 200:
            st.error("Failed to retrieve entity records.")
            return

        payload = response.json()
        records = payload.get("records", [])

        if not records:
            st.info("No records found for that entity_id.")
            return

        st.write(f"Found {len(records)} record(s) for entity_id {entity_id}")

        flat_rows = []
        for record in records:
            row = {
                "entity_id": record.get("entity_id"),
                "timestamp": record.get("timestamp"),
                **record.get("features", {}),
                **{f"meta_{k}": v for k, v in record.get("metadata", {}).items()},
            }
            flat_rows.append(row)

        df = pd.DataFrame(flat_rows)
        st.dataframe(df, use_container_width=True)

        st.write("### Raw Records")
        st.json(records)

    except Exception as exc:
        st.error(f"Failed to connect to API: {exc}")