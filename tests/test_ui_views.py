import importlib
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, mock_open, patch

import json as std_json

os.environ["API_BASE_URL"] = "http://ui-test.local:8000"
os.environ["STORAGE_PATH"] = "data/test-records.json"
os.environ["PIPELINE_SUMMARY_PATH"] = "reports/pipeline_run_summary.json"


class _FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


def _import_ui_module(module_name):
    fake_streamlit = types.SimpleNamespace()
    fake_requests = types.SimpleNamespace(get=lambda *args, **kwargs: None, post=lambda *args, **kwargs: None)
    saved_streamlit = sys.modules.get("streamlit")
    saved_requests = sys.modules.get("requests")

    try:
        sys.modules["streamlit"] = fake_streamlit
        sys.modules["requests"] = fake_requests
        sys.modules.pop("modules.streamlit_ui.views._config", None)
        sys.modules.pop(module_name, None)
        return importlib.import_module(module_name)
    finally:
        if saved_streamlit is None:
            sys.modules.pop("streamlit", None)
        else:
            sys.modules["streamlit"] = saved_streamlit

        if saved_requests is None:
            sys.modules.pop("requests", None)
        else:
            sys.modules["requests"] = saved_requests


class TestUiViews(unittest.TestCase):
    def test_upload_view_posts_to_data_endpoint(self):
        upload_module = _import_ui_module("modules.streamlit_ui.views.upload")

        uploaded_file = MagicMock()
        uploaded_file.name = "phase6_upload.csv"
        uploaded_file.getbuffer.return_value = b"entity_id,timestamp\n1,2026-03-15"

        upload_module.st = MagicMock()
        upload_module.st.file_uploader.return_value = uploaded_file
        upload_module.st.button.return_value = True
        upload_module.requests = MagicMock()
        upload_module.requests.post.return_value = _FakeResponse(status_code=200, payload={"status": "processed"})

        with patch("modules.streamlit_ui.views.upload.open", mock_open()):
            upload_module.render_upload_view()

        upload_module.requests.post.assert_called_once()
        post_url = upload_module.requests.post.call_args[0][0]
        post_json = upload_module.requests.post.call_args[1]["json"]

        self.assertEqual(post_url, "http://ui-test.local:8000/data")
        self.assertTrue(post_json["source_path"].endswith("phase6_upload.csv"))

    def test_metrics_view_renders_pipeline_summary(self):
        metrics_module = _import_ui_module("modules.streamlit_ui.views.metrics")

        metrics_module.st = MagicMock()
        metric_columns = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        metrics_module.st.columns.return_value = metric_columns
        metrics_module.requests = MagicMock()
        metrics_module.requests.get.return_value = _FakeResponse(
            payload={
                "status": "SUCCESS",
                "records_ingested": 3,
                "records_valid": 3,
                "records_invalid": 0,
                "records_persisted": 3,
            }
        )

        metrics_module.render_metrics_view()

        metrics_module.requests.get.assert_called_once_with("http://ui-test.local:8000/pipeline/status")
        self.assertTrue(metric_columns[0].metric.called)
        self.assertTrue(metric_columns[1].metric.called)
        self.assertTrue(metric_columns[2].metric.called)
        self.assertTrue(metric_columns[3].metric.called)

    def test_entity_explorer_loads_records(self):
        entity_module = _import_ui_module("modules.streamlit_ui.views.entity_explorer")

        entity_module.st = MagicMock()
        entity_module.st.text_input.return_value = "101"
        entity_module.requests = MagicMock()
        entity_module.requests.get.return_value = _FakeResponse(
            payload={
                "entity_id": "101",
                "records": [
                    {
                        "entity_id": "101",
                        "timestamp": "2026-03-15",
                        "features": {"order_amount": 11.0},
                        "metadata": {},
                    }
                ],
            }
        )

        entity_module.render_entity_explorer()

        entity_module.requests.get.assert_called_once_with("http://ui-test.local:8000/entity/101")
        self.assertTrue(entity_module.st.dataframe.called)

    def test_validation_errors_view_handles_zero_invalid(self):
        validation_module = _import_ui_module("modules.streamlit_ui.views.validation_errors")

        validation_module.st = MagicMock()
        validation_module.requests = MagicMock()
        validation_module.requests.get.return_value = _FakeResponse(payload={"records_invalid": 0})

        validation_module.render_validation_errors()

        validation_module.requests.get.assert_called_once_with("http://ui-test.local:8000/pipeline/status")
        validation_module.st.success.assert_called_once()

    def test_validation_errors_view_renders_error_breakdown(self):
        validation_module = _import_ui_module("modules.streamlit_ui.views.validation_errors")

        validation_module.st = MagicMock()
        validation_module.requests = MagicMock()
        validation_module.requests.get.return_value = _FakeResponse(payload={"records_invalid": 2})

        validation_module.render_validation_errors()

        self.assertTrue(validation_module.st.metric.called)
        self.assertTrue(validation_module.st.bar_chart.called)

    def test_anomalies_view_reads_records_and_renders(self):
        anomalies_module = _import_ui_module("modules.streamlit_ui.views.anomalies")

        anomalies_module.st = MagicMock()
        anomalies_module.st.selectbox.return_value = "order_amount"

        fake_records = [
            {
                "entity_id": "101",
                "timestamp": "2026-03-15",
                "features": {"order_amount": 10.0},
            },
            {
                "entity_id": "102",
                "timestamp": "2026-03-15",
                "features": {"order_amount": 12.0},
            },
            {
                "entity_id": "103",
                "timestamp": "2026-03-15",
                "features": {"order_amount": 200.0},
            },
        ]

        with patch("pathlib.Path.exists", return_value=True), \
            patch("builtins.open", mock_open(read_data=std_json.dumps(fake_records))):
            anomalies_module.render_anomalies_view()

        self.assertTrue(anomalies_module.st.metric.called)
        self.assertTrue(anomalies_module.st.dataframe.called)


if __name__ == "__main__":
    unittest.main()
