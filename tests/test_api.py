import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("APP_ENV", "dev")
os.environ.setdefault("APP_VERSION", "0.1.0-test")
os.environ.setdefault("PORT", "8000")
os.environ.setdefault("UPLOAD_ACCESS_CODE", "test-access-code")
os.environ.setdefault("PERSISTENCE_MODE", "json")
os.environ.setdefault("STORAGE_PATH", "data/test-records.json")
os.environ.setdefault("LOG_LEVEL", "INFO")
os.environ.setdefault("ALLOW_LOCAL_FALLBACK", "true")
os.environ.setdefault("API_BASE_URL", "http://api-test.local:8000")
os.environ.setdefault("INPUT_SOURCE_PATH", "data/opsight_sample_sales.csv")
os.environ.setdefault("PIPELINE_SUMMARY_PATH", "reports/pipeline_run_summary.json")

import modules.api.app as api_app_module
import app as root_app_module
from modules.persistence.local_storage import LocalStorage
import modules.api.routes.entities as entities_route
import modules.api.routes.status as status_route


class TestApiLayer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(api_app_module.app)
        cls.access_code = os.environ["UPLOAD_ACCESS_CODE"]
        cls.valid_headers = {"X-Upload-Access-Code": cls.access_code}

    def test_service_starts_and_health_endpoint_is_available(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "version": os.environ["APP_VERSION"]},
        )

    def test_root_asgi_entrypoint_exposes_the_api_app(self):
        self.assertIs(root_app_module.app, api_app_module.app)

    def test_ingestion_endpoint_runs_pipeline_runner(self):
        mocked_summary = {
            "status": "SUCCESS",
            "failed_stage": None,
            "records_ingested": 3,
            "records_valid": 3,
            "records_invalid": 0,
            "records_persisted": 3,
            "runtime_seconds": 0.1,
        }

        with patch("modules.api.routes.ingest.run_pipeline", return_value=mocked_summary) as mocked_runner:
            response = self.client.post(
                "/data",
                json={"source_path": "data/opsight_sample_sales.csv"},
                headers=self.valid_headers,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "processed")
        self.assertEqual(response.json()["records_ingested"], 3)
        expected_path = str((Path(__file__).resolve().parents[1] / "data" / "opsight_sample_sales.csv").resolve())
        mocked_runner.assert_called_once_with(expected_path, source_mode=None)

    def test_ingestion_endpoint_returns_500_when_pipeline_runner_fails(self):
        failed_summary = {
            "status": "FAILED",
            "failed_stage": "ingestion",
            "error_type": "blob_not_found_error",
            "error_message": "Ingestion failed - Blob not found: Blob 'csv/missing.csv' not found",
            "records_ingested": 0,
            "records_valid": 0,
            "records_invalid": 0,
            "records_persisted": 0,
            "runtime_seconds": 0.1,
        }

        with patch("modules.api.routes.ingest.run_pipeline", return_value=failed_summary):
            response = self.client.post(
                "/data",
                json={"source_path": "data/missing.csv"},
                headers=self.valid_headers,
            )

        self.assertEqual(response.status_code, 500)
        body = response.json()
        self.assertEqual(body["error"], "Request failed")
        self.assertIn("Pipeline failure at stage: ingestion", body["detail"])
        self.assertIn("Blob not found", body["detail"])

    def test_ingestion_endpoint_keeps_blob_style_source_path_unmodified(self):
        mocked_summary = {
            "status": "SUCCESS",
            "failed_stage": None,
            "records_ingested": 3,
            "records_valid": 3,
            "records_invalid": 0,
            "records_persisted": 3,
            "runtime_seconds": 0.1,
        }

        blob_source_path = "opsight-raw/csv/opsight_sample_sales.csv"

        with patch("modules.api.routes.ingest.run_pipeline", return_value=mocked_summary) as mocked_runner:
            response = self.client.post(
                "/data",
                json={"source_path": blob_source_path},
                headers=self.valid_headers,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "processed")
        mocked_runner.assert_called_once_with(blob_source_path, source_mode=None)

    def test_ingestion_endpoint_requires_source_path(self):
        response = self.client.post("/data", json={}, headers=self.valid_headers)

        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertEqual(body["error"], "Request failed")
        self.assertEqual(body["detail"], "source_path is required")

    def test_ingestion_endpoint_invalid_body_returns_validation_error(self):
        response = self.client.post("/data")

        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body["error"], "Invalid request")
        self.assertTrue(isinstance(body["detail"], list))

    def test_protected_endpoint_rejects_missing_access_code(self):
        response = self.client.post("/data", json={"source_path": "data/opsight_sample_sales.csv"})

        self.assertEqual(response.status_code, 403)
        body = response.json()
        self.assertEqual(body["error"], "Request failed")
        self.assertEqual(body["detail"], "Invalid or missing upload access code")

    def test_protected_endpoint_rejects_wrong_access_code(self):
        response = self.client.post(
            "/data",
            json={"source_path": "data/opsight_sample_sales.csv"},
            headers={"X-Upload-Access-Code": "wrong-code"},
        )

        self.assertEqual(response.status_code, 403)
        body = response.json()
        self.assertEqual(body["error"], "Request failed")
        self.assertEqual(body["detail"], "Invalid or missing upload access code")

    def test_pipeline_trigger_endpoint_accepts_empty_payload(self):
        """Phase 14: /pipeline/trigger respects target parameter for dataset selection."""
        mocked_summary = {
            "status": "SUCCESS",
            "failed_stage": None,
            "records_ingested": 2,
            "records_valid": 2,
            "records_invalid": 0,
            "records_persisted": 2,
            "runtime_seconds": 0.1,
        }

        with patch("modules.api.routes.ingest.run_pipeline", return_value=mocked_summary):
            # Send payload with target to control dataset selection
            response = self.client.post(
                "/pipeline/trigger",
                json={"target": "local", "dataset_id": "sales_csv"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "processed")

    def test_pipeline_trigger_rejects_unknown_dataset_id(self):
        response = self.client.post(
            "/pipeline/trigger",
            json={"target": "local", "dataset_id": "does_not_exist"},
        )

        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body["detail"], "Unknown dataset_id")

    def test_pipeline_trigger_sql_dataset_not_wired(self):
        response = self.client.post(
            "/pipeline/trigger",
            json={"target": "local", "dataset_id": "sales_sql"},
        )

        self.assertEqual(response.status_code, 501)
        body = response.json()
        self.assertEqual(body["detail"], "SQL dataset execution not wired yet")

    def test_protected_attempt_logging_excludes_secret(self):
        with patch("modules.api.access_control.logger.info") as mocked_info, patch(
            "modules.api.access_control.logger.warning"
        ) as mocked_warning:
            self.client.post(
                "/data",
                json={"source_path": "data/opsight_sample_sales.csv"},
                headers={"X-Upload-Access-Code": "wrong-code"},
            )

        self.assertTrue(mocked_info.called or mocked_warning.called)
        log_calls = [*mocked_info.call_args_list, *mocked_warning.call_args_list]
        protected_events = [
            kwargs.get("extra", {})
            for _, kwargs in log_calls
            if kwargs.get("extra", {}).get("event") == "protected_access_attempt"
        ]
        self.assertTrue(protected_events)
        extra = protected_events[-1]
        self.assertIn("route", extra)
        self.assertIn("access_code_valid", extra)
        self.assertFalse(extra["access_code_valid"])
        self.assertIn("timestamp", extra)
        self.assertNotIn("access_code", extra)

    def test_entity_endpoint_returns_records_for_entity(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage = LocalStorage(storage_dir=tmp_dir, filename="records.json")
            storage.save_records(
                [
                    {"entity_id": "101", "timestamp": "2026-03-12", "features": {}, "metadata": {}},
                    {"entity_id": "102", "timestamp": "2026-03-13", "features": {}, "metadata": {}},
                ]
            )

            with patch.object(entities_route, "storage", storage):
                response = self.client.get("/entity/101")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["entity_id"], "101")
        self.assertEqual(len(body["records"]), 1)
        self.assertEqual(str(body["records"][0]["entity_id"]), "101")

    def test_entity_endpoint_returns_404_for_missing_entity(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage = LocalStorage(storage_dir=tmp_dir, filename="records.json")
            storage.save_records([])

            with patch.object(entities_route, "storage", storage):
                response = self.client.get("/entity/does-not-exist")

        self.assertEqual(response.status_code, 404)
        body = response.json()
        self.assertEqual(body["error"], "Request failed")
        self.assertEqual(body["detail"], "Entity not found")

    def test_pipeline_status_endpoint_returns_report_metrics(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            summary_path = Path(tmp_dir) / "pipeline_run_summary.json"
            expected = {
                "status": "SUCCESS",
                "failed_stage": None,
                "records_ingested": 3,
                "records_valid": 2,
                "records_invalid": 1,
                "records_persisted": 2,
                "runtime_seconds": 0.01,
            }
            with open(summary_path, "w", encoding="utf-8") as file_handle:
                json.dump(expected, file_handle)

            with patch.object(status_route, "SUMMARY_PATH", summary_path):
                response = self.client.get("/pipeline/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)

    def test_pipeline_status_endpoint_reports_no_runs(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            missing_summary_path = Path(tmp_dir) / "missing_summary.json"

            with patch.object(status_route, "SUMMARY_PATH", missing_summary_path):
                response = self.client.get("/pipeline/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "no runs recorded"})


if __name__ == "__main__":
    unittest.main()
