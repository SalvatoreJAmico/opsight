import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

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

import run_pipeline


class TestRunPipeline(unittest.TestCase):
    def test_pipeline_success_writes_summary_and_persists_valid_records(self):
        canonical_records = [
            {"entity_id": "e-1", "timestamp": "2026-03-15T12:00:00", "features": {}, "metadata": {}},
            {"entity_id": "e-2", "timestamp": "2026-03-15T12:05:00", "features": {}, "metadata": {}},
        ]

        validation_results = [
            {"status": "valid", "errors": []},
            {"status": "invalid", "errors": ["Missing features"]},
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            reports_dir = Path(tmp_dir)
            reports_dir.mkdir(parents=True, exist_ok=True)
            run_summary_path = reports_dir / "pipeline_run_summary.json"
            failure_summary_path = reports_dir / "pipeline_failure_summary.json"

            storage = MagicMock()

            with patch.dict(os.environ, {"PIPELINE_SUMMARY_PATH": str(run_summary_path)}), \
                patch("run_pipeline.ingest_data", return_value=[{"id": 1}, {"id": 2}]), \
                patch("run_pipeline.adapt_records", return_value=canonical_records), \
                patch("run_pipeline.validate_canonical_record", side_effect=validation_results), \
                patch("run_pipeline.StorageFactory.create_storage", return_value=storage):

                summary = run_pipeline.run_pipeline()

            self.assertEqual(summary["status"], "SUCCESS")
            self.assertIsNone(summary["failed_stage"])
            self.assertEqual(summary["records_ingested"], 2)
            self.assertEqual(summary["records_valid"], 1)
            self.assertEqual(summary["records_invalid"], 1)
            self.assertEqual(summary["records_persisted"], 1)
            self.assertGreaterEqual(summary["runtime_seconds"], 0)

            storage.save_records.assert_called_once_with([canonical_records[0]])

            self.assertTrue(run_summary_path.exists())
            self.assertFalse(failure_summary_path.exists())

            with open(run_summary_path, "r", encoding="utf-8") as file_handle:
                summary_on_disk = json.load(file_handle)

            self.assertEqual(summary_on_disk["status"], "SUCCESS")
            self.assertEqual(summary_on_disk["records_valid"], 1)

    def test_pipeline_failure_sets_failed_stage_and_writes_failure_summary(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            reports_dir = Path(tmp_dir)
            reports_dir.mkdir(parents=True, exist_ok=True)
            run_summary_path = reports_dir / "pipeline_run_summary.json"
            failure_summary_path = reports_dir / "pipeline_failure_summary.json"

            with patch.dict(os.environ, {"PIPELINE_SUMMARY_PATH": str(run_summary_path)}), \
                patch("run_pipeline.ingest_data", side_effect=RuntimeError("broken source")):

                summary = run_pipeline.run_pipeline()

            self.assertEqual(summary["status"], "FAILED")
            self.assertEqual(summary["failed_stage"], "ingestion")
            self.assertEqual(summary["records_ingested"], 0)
            self.assertEqual(summary["records_valid"], 0)
            self.assertEqual(summary["records_invalid"], 0)
            self.assertEqual(summary["records_persisted"], 0)
            self.assertGreaterEqual(summary["runtime_seconds"], 0)

            self.assertTrue(run_summary_path.exists())
            self.assertTrue(failure_summary_path.exists())

            with open(failure_summary_path, "r", encoding="utf-8") as file_handle:
                failure_summary_on_disk = json.load(file_handle)

            self.assertEqual(failure_summary_on_disk["status"], "FAILED")
            self.assertEqual(failure_summary_on_disk["failed_stage"], "ingestion")

    def test_pipeline_persistence_failure_reports_failed_stage(self):
        canonical_records = [
            {"entity_id": "e-1", "timestamp": "2026-03-15T12:00:00", "features": {}, "metadata": {}},
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            reports_dir = Path(tmp_dir)
            reports_dir.mkdir(parents=True, exist_ok=True)
            run_summary_path = reports_dir / "pipeline_run_summary.json"
            failure_summary_path = reports_dir / "pipeline_failure_summary.json"

            storage = MagicMock()
            storage.save_records.side_effect = RuntimeError("disk full")

            with patch.dict(os.environ, {"PIPELINE_SUMMARY_PATH": str(run_summary_path)}), \
                patch("run_pipeline.ingest_data", return_value=[{"id": 1}]), \
                patch("run_pipeline.adapt_records", return_value=canonical_records), \
                patch("run_pipeline.validate_canonical_record", return_value={"status": "valid", "errors": []}), \
                patch("run_pipeline.StorageFactory.create_storage", return_value=storage):

                summary = run_pipeline.run_pipeline()

            self.assertEqual(summary["status"], "FAILED")
            self.assertEqual(summary["failed_stage"], "persistence")
            self.assertEqual(summary["records_ingested"], 1)
            self.assertEqual(summary["records_valid"], 1)
            self.assertEqual(summary["records_invalid"], 0)
            self.assertEqual(summary["records_persisted"], 0)
            self.assertGreaterEqual(summary["runtime_seconds"], 0)

            self.assertTrue(run_summary_path.exists())
            self.assertTrue(failure_summary_path.exists())

            with open(failure_summary_path, "r", encoding="utf-8") as file_handle:
                failure_summary_on_disk = json.load(file_handle)

            self.assertEqual(failure_summary_on_disk["status"], "FAILED")
            self.assertEqual(failure_summary_on_disk["failed_stage"], "persistence")

    def test_pipeline_adapter_failure_reports_failed_stage(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            reports_dir = Path(tmp_dir)
            reports_dir.mkdir(parents=True, exist_ok=True)
            run_summary_path = reports_dir / "pipeline_run_summary.json"
            failure_summary_path = reports_dir / "pipeline_failure_summary.json"

            with patch.dict(os.environ, {"PIPELINE_SUMMARY_PATH": str(run_summary_path)}), \
                patch("run_pipeline.ingest_data", return_value=[{"id": 1}]), \
                patch("run_pipeline.adapt_records", side_effect=RuntimeError("bad mapping")):

                summary = run_pipeline.run_pipeline()

            self.assertEqual(summary["status"], "FAILED")
            self.assertEqual(summary["failed_stage"], "adapter")
            self.assertEqual(summary["records_ingested"], 1)
            self.assertEqual(summary["records_valid"], 0)
            self.assertEqual(summary["records_invalid"], 0)
            self.assertEqual(summary["records_persisted"], 0)
            self.assertGreaterEqual(summary["runtime_seconds"], 0)

            self.assertTrue(run_summary_path.exists())
            self.assertTrue(failure_summary_path.exists())

            with open(failure_summary_path, "r", encoding="utf-8") as file_handle:
                failure_summary_on_disk = json.load(file_handle)

            self.assertEqual(failure_summary_on_disk["status"], "FAILED")
            self.assertEqual(failure_summary_on_disk["failed_stage"], "adapter")

    def test_pipeline_validation_failure_reports_failed_stage(self):
        canonical_records = [
            {"entity_id": "e-1", "timestamp": "2026-03-15T12:00:00", "features": {}, "metadata": {}},
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            reports_dir = Path(tmp_dir)
            reports_dir.mkdir(parents=True, exist_ok=True)
            run_summary_path = reports_dir / "pipeline_run_summary.json"
            failure_summary_path = reports_dir / "pipeline_failure_summary.json"

            with patch.dict(os.environ, {"PIPELINE_SUMMARY_PATH": str(run_summary_path)}), \
                patch("run_pipeline.ingest_data", return_value=[{"id": 1}]), \
                patch("run_pipeline.adapt_records", return_value=canonical_records), \
                patch("run_pipeline.validate_canonical_record", side_effect=RuntimeError("validator crashed")):

                summary = run_pipeline.run_pipeline()

            self.assertEqual(summary["status"], "FAILED")
            self.assertEqual(summary["failed_stage"], "validation")
            self.assertEqual(summary["records_ingested"], 1)
            self.assertEqual(summary["records_valid"], 0)
            self.assertEqual(summary["records_invalid"], 0)
            self.assertEqual(summary["records_persisted"], 0)
            self.assertGreaterEqual(summary["runtime_seconds"], 0)

            self.assertTrue(run_summary_path.exists())
            self.assertTrue(failure_summary_path.exists())

            with open(failure_summary_path, "r", encoding="utf-8") as file_handle:
                failure_summary_on_disk = json.load(file_handle)

            self.assertEqual(failure_summary_on_disk["status"], "FAILED")
            self.assertEqual(failure_summary_on_disk["failed_stage"], "validation")


if __name__ == "__main__":
    unittest.main()
