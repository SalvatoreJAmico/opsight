import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pandas as pd

from fastapi import HTTPException
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
os.environ.setdefault("CORS_ALLOWED_ORIGINS", "http://localhost:5173")

import modules.api.app as api_app_module
import app as root_app_module
from modules.api.dataset_config import DATASET_MAP
from modules.persistence.local_storage import LocalStorage
import modules.api.routes.entities as entities_route
import modules.api.routes.status as status_route
import modules.api.session_state as session_state


class TestApiLayer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(api_app_module.app)
        cls.access_code = os.environ["UPLOAD_ACCESS_CODE"]
        cls.valid_headers = {"X-Upload-Access-Code": cls.access_code}

    def setUp(self):
        session_state.reset_session_state()

    def test_service_starts_and_health_endpoint_is_available(self):
        # The .env file has SQL configured, so we patch it to test the no-SQL case
        with patch("modules.api.app.SQL_CONFIGURED", False):
            response = self.client.get("/health")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.json(),
                {
                    "status": "ok",
                    "version": os.environ["APP_VERSION"],
                    "sql_configured": False,
                },
            )

    def test_preflight_request_returns_cors_headers_for_allowed_origin(self):
        response = self.client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("access-control-allow-origin"),
            "http://localhost:5173",
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
        mocked_runner.assert_called_once_with(expected_path, source_mode=None, data_format=None)

    def test_ingestion_endpoint_success_updates_session_pipeline_status_completed(self):
        mocked_summary = {
            "status": "SUCCESS",
            "failed_stage": None,
            "records_ingested": 3,
            "records_valid": 3,
            "records_invalid": 0,
            "records_persisted": 3,
            "runtime_seconds": 0.1,
        }

        with patch("modules.api.routes.ingest.run_pipeline", return_value=mocked_summary):
            response = self.client.post(
                "/data",
                json={"source_path": "data/opsight_sample_sales.csv"},
                headers=self.valid_headers,
            )

        self.assertEqual(response.status_code, 200)
        state = session_state.get_session_state()
        self.assertEqual(state["pipeline_status"], "completed")

    def test_ingestion_endpoint_failure_updates_session_pipeline_status_failed(self):
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
        state = session_state.get_session_state()
        self.assertEqual(state["pipeline_status"], "failed")

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
        mocked_runner.assert_called_once_with(blob_source_path, source_mode=None, data_format=None)

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
        self.assertEqual(body["detail"], "Invalid or missing dataset access code")

    def test_protected_endpoint_rejects_wrong_access_code(self):
        response = self.client.post(
            "/data",
            json={"source_path": "data/opsight_sample_sales.csv"},
            headers={"X-Upload-Access-Code": "wrong-code"},
        )

        self.assertEqual(response.status_code, 403)
        body = response.json()
        self.assertEqual(body["error"], "Request failed")
        self.assertEqual(body["detail"], "Invalid or missing dataset access code")

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

    def test_pipeline_trigger_uses_selected_blob_dataset_path(self):
        mocked_summary = {
            "status": "SUCCESS",
            "failed_stage": None,
            "records_ingested": 2,
            "records_valid": 2,
            "records_invalid": 0,
            "records_persisted": 2,
            "runtime_seconds": 0.1,
        }

        with patch("modules.api.routes.ingest.run_pipeline", return_value=mocked_summary) as mocked_runner:
            response = self.client.post(
                "/pipeline/trigger",
                json={"target": "cloud", "dataset_id": "transactions_json"},
            )

        self.assertEqual(response.status_code, 200)
        mocked_runner.assert_called_once_with(
            DATASET_MAP["transactions_json"]["path"],
            source_mode=None,
            data_format="json",
        )

    def test_pipeline_trigger_does_not_use_old_sample_blob_path(self):
        mocked_summary = {
            "status": "SUCCESS",
            "failed_stage": None,
            "records_ingested": 2,
            "records_valid": 2,
            "records_invalid": 0,
            "records_persisted": 2,
            "runtime_seconds": 0.1,
        }

        with patch("modules.api.routes.ingest.run_pipeline", return_value=mocked_summary) as mocked_runner:
            response = self.client.post(
                "/pipeline/trigger",
                json={"target": "local", "dataset_id": "sales_csv"},
            )

        self.assertEqual(response.status_code, 200)
        called_source_path = mocked_runner.call_args.args[0]
        self.assertEqual(called_source_path, DATASET_MAP["sales_csv"]["path"])
        self.assertNotEqual(called_source_path, "opsight-raw/csv/opsight_sample_sales.csv")
        self.assertNotEqual(called_source_path, "csv/opsight_sample_sales.csv")

    def test_pipeline_trigger_success_updates_session_pipeline_status_completed(self):
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
            response = self.client.post(
                "/pipeline/trigger",
                json={"target": "local", "dataset_id": "sales_csv"},
            )

        self.assertEqual(response.status_code, 200)
        state = session_state.get_session_state()
        self.assertEqual(state["active_dataset"], "sales_csv")
        self.assertEqual(state["dataset_source_metadata"]["dataset_id"], "sales_csv")
        self.assertEqual(state["dataset_source_metadata"]["source_type"], "blob")
        self.assertEqual(state["pipeline_status"], "completed")

    def test_pipeline_trigger_failure_updates_session_pipeline_status_failed(self):
        failed_summary = {
            "status": "FAILED",
            "failed_stage": "validation",
            "error_type": "validation_error",
            "error_message": "Validation failed",
            "records_ingested": 5,
            "records_valid": 0,
            "records_invalid": 5,
            "records_persisted": 0,
            "runtime_seconds": 0.1,
        }

        with patch("modules.api.routes.ingest.run_pipeline", return_value=failed_summary):
            response = self.client.post(
                "/pipeline/trigger",
                json={"target": "local", "dataset_id": "sales_csv"},
            )

        self.assertEqual(response.status_code, 500)
        state = session_state.get_session_state()
        self.assertEqual(state["active_dataset"], "sales_csv")
        self.assertEqual(state["dataset_source_metadata"], None)
        self.assertEqual(state["pipeline_status"], "failed")

    def test_pipeline_trigger_rejects_unknown_dataset_id(self):
        response = self.client.post(
            "/pipeline/trigger",
            json={"target": "local", "dataset_id": "does_not_exist"},
        )

        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body["detail"], "Unknown dataset_id")

    def test_pipeline_trigger_sql_dataset_runs(self):
        session_state.set_active_dataset("sales_csv")
        session_state.set_pipeline_status("completed")

        mocked_summary = {
            "status": "SUCCESS",
            "failed_stage": None,
            "records_ingested": 5,
            "records_valid": 5,
            "records_invalid": 0,
            "records_persisted": 5,
            "runtime_seconds": 0.1,
        }

        with patch("modules.api.routes.ingest.run_pipeline", return_value=mocked_summary):
            response = self.client.post(
                "/pipeline/trigger",
                json={"target": "local", "dataset_id": "sales_sql"},
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["dataset_id"], "sales_sql")
        self.assertEqual(body["dataset_source_type"], "sql")
        self.assertEqual(body["dataset_schema"], "dbo")
        self.assertEqual(body["dataset_table"], "Orders")
        self.assertEqual(body["dataset_source_name"], "Northwind Orders Table")
        self.assertEqual(body["dataset_source_location"], "sql://Northwind/dbo/Orders")
        state = session_state.get_session_state()
        self.assertEqual(state["active_dataset"], "sales_sql")
        self.assertEqual(state["dataset_source_metadata"]["dataset_id"], "sales_sql")
        self.assertEqual(state["pipeline_status"], "completed")

    def test_session_state_endpoint_returns_current_state(self):
        session_state.set_active_dataset("transactions_json")
        session_state.set_pipeline_status("running")
        session_state.set_anomaly_status("completed")
        session_state.set_prediction_status("running")

        response = self.client.get("/session/state")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "active_dataset": "transactions_json",
                "dataset_source_metadata": None,
                "pipeline_status": "running",
                "anomaly_status": "completed",
                "prediction_status": "running",
                "selected_variables": {"target": None, "compare": []},
            },
        )

    def test_sql_start_endpoint_returns_ready_when_connection_succeeds(self):
        with patch("modules.api.routes.status.load_runtime_config", return_value=SimpleNamespace(sql_connection_string="mssql+pyodbc://x")), \
            patch("modules.api.routes.status._probe_sql_connection", return_value=None):
            response = self.client.post("/sql/start", json={"target": "local"})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get("ready"))
        self.assertEqual(response.json().get("message"), "SQL Server is ready")

    def test_sql_start_endpoint_fails_when_connection_string_missing(self):
        with patch("modules.api.routes.status.load_runtime_config", return_value=SimpleNamespace(sql_connection_string=None)):
            response = self.client.post("/sql/start", json={"target": "local"})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json().get("ready"))
        self.assertEqual(response.json().get("message"), "SQL connection string not configured")

    def test_sql_start_endpoint_starts_server_when_initial_probe_fails(self):
        with patch("modules.api.routes.status.load_runtime_config", return_value=SimpleNamespace(sql_connection_string="mssql+pyodbc://x")), \
            patch(
                "modules.api.routes.status._probe_sql_connection",
                side_effect=[RuntimeError("HYT00 login timeout expired"), None],
            ), \
            patch("modules.api.routes.status._run_sql_start_command", return_value=(True, "startup triggered")):
            response = self.client.post("/sql/start", json={"target": "local"})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get("ready"))
        self.assertEqual(response.json().get("message"), "SQL Server started and is ready")

    def test_sql_start_endpoint_reports_error_when_startup_unavailable(self):
        with patch("modules.api.routes.status.load_runtime_config", return_value=SimpleNamespace(sql_connection_string="mssql+pyodbc://x")), \
            patch("modules.api.routes.status._probe_sql_connection", side_effect=RuntimeError("HYT00 login timeout expired")), \
            patch(
                "modules.api.routes.status._run_sql_start_command",
                return_value=(False, "No SQL startup method is configured"),
            ):
            response = self.client.post("/sql/start", json={"target": "local"})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json().get("ready"))
        self.assertIn("No SQL startup method is configured", response.json().get("message"))

    def test_sql_start_endpoint_cloud_mode_wakes_database_by_retrying_probe(self):
        with patch("modules.api.routes.status.load_runtime_config", return_value=SimpleNamespace(sql_connection_string="mssql+pyodbc://x")), \
            patch(
                "modules.api.routes.status._probe_sql_connection",
                side_effect=[RuntimeError("HYT00 login timeout expired"), None],
            ):
            response = self.client.post("/sql/start", json={"target": "cloud"})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get("ready"))
        self.assertEqual(response.json().get("message"), "SQL Server started and is ready")

    def test_sql_start_endpoint_cloud_mode_reports_start_failure(self):
        with patch("modules.api.routes.status.load_runtime_config", return_value=SimpleNamespace(sql_connection_string="mssql+pyodbc://x")), \
            patch("modules.api.routes.status._probe_sql_connection", side_effect=RuntimeError("HYT00 login timeout expired")), \
            patch("modules.api.routes.status._wait_for_sql_ready", return_value=RuntimeError("HYT00 login timeout expired")):
            response = self.client.post("/sql/start", json={"target": "cloud"})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json().get("ready"))
        self.assertEqual(
            response.json().get("message"),
            "The cloud database is still starting. Please wait a moment and try again.",
        )

    def test_session_reset_clears_storage_and_resets_session_state(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage_path = Path(tmp_dir) / "records.json"
            local_storage = LocalStorage(storage_path=str(storage_path))
            local_storage.save_records([
                {"entity_id": "101", "timestamp": "2026-03-12", "features": {"value": 10}, "metadata": {}},
            ])

            session_state.set_active_dataset("sales_csv")
            session_state.set_pipeline_status("completed")
            session_state.set_anomaly_status("completed")
            session_state.set_prediction_status("completed")

            with patch("modules.api.routes.status.StorageConfig") as mocked_storage_config:
                mocked_storage_config.return_value.storage_path = str(storage_path)
                response = self.client.post("/session/reset")

            reloaded_storage = LocalStorage(storage_path=str(storage_path))
            self.assertEqual(reloaded_storage.load_records(), [])

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "reset")
        self.assertEqual(
            body["session"],
            {
                "active_dataset": None,
                "dataset_source_metadata": None,
                "pipeline_status": "not_run",
                "anomaly_status": "idle",
                "prediction_status": "idle",
                "selected_variables": {"target": None, "compare": []},
            },
        )

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

    def test_charts_overview_returns_complete_dataset_summary(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage_path = Path(tmp_dir) / "records.json"
            local_storage = LocalStorage(storage_path=str(storage_path))
            local_storage.save_records(
                [
                    {
                        "entity_id": "1",
                        "timestamp": "2026-01-01",
                        "features": {"sales": 100.0, "profit": 20.0, "category": "Furniture"},
                        "metadata": {},
                    },
                    {
                        "entity_id": "2",
                        "timestamp": "2026-01-02",
                        "features": {"sales": 200.0, "profit": None, "category": "Office Supplies"},
                        "metadata": {},
                    },
                    {
                        "entity_id": "3",
                        "timestamp": "2026-01-03",
                        "features": {"sales": None, "profit": 15.0, "category": "Furniture"},
                        "metadata": {},
                    },
                ]
            )

            session_state.set_active_dataset("sales_csv")
            session_state.set_dataset_source_metadata(
                {
                    "dataset_id": "sales_csv",
                    "source_type": "blob",
                    "source_name": "Superstore Sales Dataset",
                    "source_url": "https://www.kaggle.com/datasets/vivek468/superstore-dataset-final",
                    "source_location": "opsight-raw/csv/Sample - Superstore.csv",
                }
            )

            with patch("modules.api.app.StorageConfig") as mocked_storage_config:
                mocked_storage_config.return_value.storage_path = str(storage_path)
                response = self.client.get("/charts/overview")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["shape"], {"rows": 3, "columns": 5})
        self.assertEqual(body["source"], "Superstore Sales Dataset")
        self.assertEqual(body["missing_by_column"]["Sales"], 1)
        self.assertEqual(body["missing_by_column"]["Profit"], 1)
        self.assertEqual(body["fields"], ["Sales", "Profit", "Category", "Order Date"])
        self.assertEqual(body["assignment_analysis"]["target_variable"], "Sales")
        self.assertEqual(
            body["assignment_analysis"]["compare_options"],
            ["Profit", "Category", "Order Date"],
        )

        numeric_fields = {item["field"] for item in body["numeric_summary"]}
        self.assertIn("Sales", numeric_fields)
        self.assertIn("Profit", numeric_fields)

        date_summary = next(item for item in body["date_summary"] if item["field"] == "Order Date")
        self.assertEqual(date_summary["count"], 3)
        self.assertEqual(date_summary["min_date"], "2026-01-01")
        self.assertEqual(date_summary["max_date"], "2026-01-03")

        categorical = next(item for item in body["categorical_summary"] if item["field"] == "Category")
        self.assertEqual(categorical["unique"], 2)
        self.assertEqual(categorical["top_values"][0]["value"], "Furniture")

    def test_cleaning_audit_returns_before_after_metrics(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage_path = Path(tmp_dir) / "records.json"
            local_storage = LocalStorage(storage_path=str(storage_path))
            local_storage.save_records(
                [
                    {
                        "entity_id": "1",
                        "timestamp": "2026-01-01",
                        "features": {"sales": 100.0, "profit": 20.0, "category": "Furniture"},
                        "metadata": {},
                    },
                    {
                        "entity_id": "2",
                        "timestamp": "2026-01-03",
                        "features": {"sales": 300.0, "profit": 40.0, "category": "Office Supplies"},
                        "metadata": {},
                    },
                ]
            )

            raw_dataframe = pd.DataFrame(
                [
                    {"id": "1", "order_date": "2026-01-01", "sales": 100.0, "profit": 20.0, "category": "Furniture"},
                    {"id": "1", "order_date": "2026-01-01", "sales": 100.0, "profit": 20.0, "category": "Furniture"},
                    {"id": "2", "order_date": None, "sales": 300.0, "profit": 40.0, "category": "Office Supplies"},
                    {"id": "3", "order_date": "2026-01-05", "sales": 500.0, "profit": None, "category": "Technology"},
                ]
            )

            session_state.set_active_dataset("sales_csv")
            session_state.set_dataset_source_metadata(
                {
                    "dataset_id": "sales_csv",
                    "source_type": "blob",
                    "source_name": "Superstore Sales Dataset",
                    "source_url": "https://www.kaggle.com/datasets/vivek468/superstore-dataset-final",
                    "source_location": "opsight-raw/csv/Sample - Superstore.csv",
                }
            )

            with patch("modules.api.app.StorageConfig") as mocked_storage_config, patch(
                "modules.api.app.ingest_data",
                return_value=raw_dataframe,
            ):
                mocked_storage_config.return_value.storage_path = str(storage_path)
                response = self.client.get("/cleaning/audit")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["row_counts"], {"before": 4, "after": 2})
        self.assertEqual(body["duplicates"]["before"], 1)
        self.assertEqual(body["duplicates"]["after"], 0)
        self.assertEqual(body["invalid_rows_removed"]["count"], 1)
        self.assertIn("Missing timestamp", body["invalid_rows_removed"]["reason_counts"])

    def test_kmeans_anomaly_endpoint_returns_summary_from_persisted_records(self):
        mocked_records = [
            {"entity_id": "1", "timestamp": "2026-03-01", "value": 10.0},
            {"entity_id": "2", "timestamp": "2026-03-02", "value": 11.0},
            {"entity_id": "3", "timestamp": "2026-03-03", "value": 12.0},
            {"entity_id": "4", "timestamp": "2026-03-04", "value": 13.0},
            {"entity_id": "5", "timestamp": "2026-03-05", "value": 80.0},
        ]

        with patch("modules.api.routes.ml._load_ml_records", return_value=mocked_records):
            response = self.client.get("/ml/anomaly/kmeans")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "completed")
        self.assertEqual(body["total"], 5)
        self.assertEqual(body["summary"]["total_records"], 5)
        self.assertIn("anomalies", body)
        self.assertEqual(body["anomalies"], body["summary"]["anomaly_count"])
        self.assertEqual(body["notes"], "K-Means clustering using distance from centroid.")
        self.assertEqual(len(body["result"]), 5)

    def test_kmeans_anomaly_endpoint_returns_422_when_no_dataset_loaded(self):
        with patch(
            "modules.api.routes.ml._load_ml_records",
            side_effect=HTTPException(status_code=422, detail="No dataset loaded. Select and run a dataset first."),
        ):
            response = self.client.get("/ml/anomaly/kmeans")

        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertEqual(body["error"], "Request failed")
        self.assertEqual(body["detail"], "No dataset loaded. Select and run a dataset first.")

    def test_anomaly_detection_endpoints_handle_nan_values_in_dataset(self):
        """Test that anomaly detection endpoints handle NaN values in dataset and produce valid JSON output."""
        import math
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage_path = Path(tmp_dir) / "records.json"
            local_storage = LocalStorage(storage_path=str(storage_path))
            # Create records with mixed NaN and valid values
            local_storage.save_records([
                {"entity_id": "1", "timestamp": "2026-01-01", "features": {"value": 10.5}, "metadata": {}},
                {"entity_id": "2", "timestamp": "2026-01-02", "features": {"value": float('nan')}, "metadata": {}},
                {"entity_id": "3", "timestamp": "2026-01-03", "features": {"value": 20.3}, "metadata": {}},
                {"entity_id": "4", "timestamp": "2026-01-04", "features": {"value": float('nan')}, "metadata": {}},
                {"entity_id": "5", "timestamp": "2026-01-05", "features": {"value": 15.8}, "metadata": {}},
            ])

            with patch("modules.api.routes.ml.StorageConfig") as mocked_config:
                mocked_config.return_value.storage_path = str(storage_path)
                
                # Test Z-Score anomaly detection
                response = self.client.get("/ml/anomaly/zscore")
                self.assertEqual(response.status_code, 200)
                body = response.json()
                self.assertIn("result", body)
                self.assertIn("summary", body)
                # Ensure no NaN or Inf values in result
                for result in body["result"]:
                    if result.get("anomaly_score") is not None:
                        self.assertFalse(math.isnan(result["anomaly_score"]))
                        self.assertFalse(math.isinf(result["anomaly_score"]))

    def test_isolation_forest_endpoint_handles_nan_values(self):
        """Test that Isolation Forest endpoint handles NaN values correctly."""
        import math
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage_path = Path(tmp_dir) / "records.json"
            local_storage = LocalStorage(storage_path=str(storage_path))
            # Create records with NaN values
            local_storage.save_records([
                {"entity_id": "1", "timestamp": "2026-01-01", "features": {"value": 100.0}, "metadata": {}},
                {"entity_id": "2", "timestamp": "2026-01-02", "features": {"value": float('nan')}, "metadata": {}},
                {"entity_id": "3", "timestamp": "2026-01-03", "features": {"value": 105.0}, "metadata": {}},
                {"entity_id": "4", "timestamp": "2026-01-04", "features": {"value": float('nan')}, "metadata": {}},
                {"entity_id": "5", "timestamp": "2026-01-05", "features": {"value": 110.0}, "metadata": {}},
                {"entity_id": "6", "timestamp": "2026-01-06", "features": {"value": 500.0}, "metadata": {}},  # outlier
            ])

            with patch("modules.api.routes.ml.StorageConfig") as mocked_config:
                mocked_config.return_value.storage_path = str(storage_path)
                
                response = self.client.get("/ml/anomaly/isolation-forest")
                self.assertEqual(response.status_code, 200)
                body = response.json()
                self.assertIn("result", body)
                self.assertIn("summary", body)
                # Ensure no NaN or Inf values in result (they should be None)
                for result in body["result"]:
                    if result.get("anomaly_score") is not None:
                        score = result["anomaly_score"]
                        self.assertFalse(isinstance(score, float) and math.isnan(score))

    def test_regression_endpoint_handles_nan_values(self):
        """Test that Linear Regression endpoint handles NaN values and produces valid JSON."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage_path = Path(tmp_dir) / "records.json"
            local_storage = LocalStorage(storage_path=str(storage_path))
            # Create records with NaN values
            local_storage.save_records([
                {"entity_id": "1", "timestamp": "2026-01-01", "features": {"value": 10.0}, "metadata": {}},
                {"entity_id": "2", "timestamp": "2026-01-02", "features": {"value": float('nan')}, "metadata": {}},
                {"entity_id": "3", "timestamp": "2026-01-03", "features": {"value": 20.0}, "metadata": {}},
                {"entity_id": "4", "timestamp": "2026-01-04", "features": {"value": float('nan')}, "metadata": {}},
                {"entity_id": "5", "timestamp": "2026-01-05", "features": {"value": 30.0}, "metadata": {}},
            ])

            with patch("modules.api.routes.ml.StorageConfig") as mocked_config:
                mocked_config.return_value.storage_path = str(storage_path)
                
                response = self.client.get("/ml/prediction/regression?steps_ahead=2")
                self.assertEqual(response.status_code, 200)
                body = response.json()
                self.assertIn("result", body)
                # Verify all predictions have valid numeric values
                for result in body["result"]:
                    self.assertIsNotNone(result.get("value"))
                    value = result["value"]
                    if isinstance(value, float):
                        import math
                        self.assertFalse(math.isnan(value))

    def test_moving_average_endpoint_handles_nan_values(self):
        """Test that Moving Average endpoint handles NaN values correctly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage_path = Path(tmp_dir) / "records.json"
            local_storage = LocalStorage(storage_path=str(storage_path))
            # Create records with NaN values
            local_storage.save_records([
                {"entity_id": "1", "timestamp": "2026-01-01", "features": {"value": 100.0}, "metadata": {}},
                {"entity_id": "2", "timestamp": "2026-01-02", "features": {"value": float('nan')}, "metadata": {}},
                {"entity_id": "3", "timestamp": "2026-01-03", "features": {"value": 110.0}, "metadata": {}},
                {"entity_id": "4", "timestamp": "2026-01-04", "features": {"value": float('nan')}, "metadata": {}},
                {"entity_id": "5", "timestamp": "2026-01-05", "features": {"value": 105.0}, "metadata": {}},
            ])

            with patch("modules.api.routes.ml.StorageConfig") as mocked_config:
                mocked_config.return_value.storage_path = str(storage_path)
                
                response = self.client.get("/ml/prediction/moving-average?steps_ahead=3")
                self.assertEqual(response.status_code, 200)
                body = response.json()
                self.assertIn("result", body)
                # Verify all predictions have valid values
                for result in body["result"]:
                    value = result.get("value")
                    if isinstance(value, float):
                        import math
                        self.assertFalse(math.isnan(value))

    def test_variable_selection_get_returns_empty_default(self):
        response = self.client.get("/variables/selection")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIsNone(body["target"])
        self.assertEqual(body["compare"], [])

    def test_variable_selection_post_saves_and_returns_selection(self):
        payload = {"target": "Sales", "compare": ["Profit", "Quantity"]}
        response = self.client.post("/variables/selection", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["target"], "Sales")
        self.assertEqual(body["compare"], ["Profit", "Quantity"])

        get_response = self.client.get("/variables/selection")
        get_body = get_response.json()
        self.assertEqual(get_body["target"], "Sales")
        self.assertEqual(get_body["compare"], ["Profit", "Quantity"])

    def test_variable_selection_post_rejects_invalid_compare_type(self):
        response = self.client.post("/variables/selection", json={"target": "Sales", "compare": "Profit"})

        self.assertEqual(response.status_code, 422)

    def test_variable_selection_post_rejects_non_string_target(self):
        response = self.client.post("/variables/selection", json={"target": 42, "compare": []})

        self.assertEqual(response.status_code, 422)

    def test_variable_selection_is_reset_with_session(self):
        self.client.post("/variables/selection", json={"target": "Sales", "compare": ["Profit"]})
        self.client.post("/session/reset")

        response = self.client.get("/variables/selection")
        body = response.json()
        self.assertIsNone(body["target"])
        self.assertEqual(body["compare"], [])


if __name__ == "__main__":
    unittest.main()
