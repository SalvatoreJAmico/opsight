import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import modules.api.app as api_app_module
from modules.persistence.local_storage import LocalStorage
import modules.api.routes.entities as entities_route
import modules.api.routes.status as status_route


class TestApiLayer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(api_app_module.app)

    def test_service_starts_and_health_endpoint_is_available(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

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
            response = self.client.post("/data", json={"source_path": "data/opsight_sample_sales.csv"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "processed")
        self.assertEqual(response.json()["records_ingested"], 3)
        mocked_runner.assert_called_once_with("data/opsight_sample_sales.csv")

    def test_ingestion_endpoint_returns_500_when_pipeline_runner_fails(self):
        failed_summary = {
            "status": "FAILED",
            "failed_stage": "ingestion",
            "records_ingested": 0,
            "records_valid": 0,
            "records_invalid": 0,
            "records_persisted": 0,
            "runtime_seconds": 0.1,
        }

        with patch("modules.api.routes.ingest.run_pipeline", return_value=failed_summary):
            response = self.client.post("/data", json={"source_path": "data/missing.csv"})

        self.assertEqual(response.status_code, 500)
        body = response.json()
        self.assertEqual(body["error"], "Request failed")
        self.assertIn("Pipeline failure at stage: ingestion", body["detail"])

    def test_ingestion_endpoint_requires_source_path(self):
        response = self.client.post("/data", json={})

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
