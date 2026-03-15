import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.pipeline.runner import run_pipeline, _convert_record, _to_native
from modules.config.storage_config import StorageConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_temp_csv(directory, content):
    """Write a CSV string to a temporary file and return its path."""
    path = os.path.join(directory, "test_source.csv")
    with open(path, "w") as fh:
        fh.write(content)
    return path


VALID_CSV = (
    "customer_id,event_timestamp,amount,region\n"
    "cust-001,2026-01-01T10:00:00,100.0,north\n"
    "cust-002,2026-01-02T11:00:00,200.0,south\n"
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestNativeConversion(unittest.TestCase):
    """Unit tests for the type-conversion helpers."""

    def test_plain_value_returned_unchanged(self):
        self.assertEqual(_to_native("hello"), "hello")
        self.assertEqual(_to_native(42), 42)

    def test_numpy_scalar_converted(self):
        try:
            import numpy as np
            value = np.int64(7)
            self.assertEqual(_to_native(value), 7)
            self.assertIsInstance(_to_native(value), int)
        except ImportError:
            self.skipTest("numpy not installed")

    def test_convert_record_returns_native_types(self):
        record = {
            "entity_id": "e1",
            "timestamp": "2026-01-01T00:00:00",
            "features": {"x": 1},
            "metadata": {},
        }
        converted = _convert_record(record)
        self.assertEqual(converted["entity_id"], "e1")
        self.assertEqual(converted["features"]["x"], 1)


class TestRunPipeline(unittest.TestCase):
    """Integration-style tests for run_pipeline."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.csv_path = _write_temp_csv(self.tmpdir, VALID_CSV)
        self.config = StorageConfig(backend="json")

    def _run_with_mock_persist(self):
        """Run the pipeline with persistence mocked out."""
        with patch(
            "modules.pipeline.runner.PersistenceManager.persist_records"
        ) as mock_persist:
            mock_persist.return_value = None
            summary = run_pipeline(self.csv_path, self.config)
        return summary

    # ------------------------------------------------------------------
    # Successful execution
    # ------------------------------------------------------------------

    def test_pipeline_returns_success_status(self):
        summary = self._run_with_mock_persist()
        self.assertEqual(summary["status"], "success")

    def test_pipeline_summary_has_required_fields(self):
        summary = self._run_with_mock_persist()
        required_fields = [
            "started_at", "ended_at", "source_path",
            "stages", "records_ingested", "records_adapted",
            "records_valid", "records_invalid", "duplicates_found",
            "records_persisted", "status", "errors",
        ]
        for field in required_fields:
            self.assertIn(field, summary, f"Missing summary field: {field}")

    def test_pipeline_ingests_correct_record_count(self):
        summary = self._run_with_mock_persist()
        self.assertEqual(summary["records_ingested"], 2)

    def test_pipeline_adapted_count_matches_ingested(self):
        summary = self._run_with_mock_persist()
        self.assertEqual(summary["records_adapted"], summary["records_ingested"])

    def test_pipeline_all_stages_complete(self):
        summary = self._run_with_mock_persist()
        for stage in ("ingestion", "adapter", "validation", "persistence"):
            self.assertEqual(
                summary["stages"].get(stage), "complete",
                f"Stage not complete: {stage}",
            )

    def test_pipeline_no_duplicates_in_unique_data(self):
        summary = self._run_with_mock_persist()
        self.assertEqual(summary["duplicates_found"], 0)

    def test_pipeline_no_errors_on_valid_data(self):
        summary = self._run_with_mock_persist()
        self.assertEqual(summary["errors"], [])

    def test_validation_runs_before_persistence(self):
        """Validation stage must complete before persistence stage."""
        completed_stages = []

        import modules.pipeline.runner as runner_mod

        original_validate = runner_mod.validate_batch
        original_persist = runner_mod.PersistenceManager.persist_records

        def mock_validate(records):
            completed_stages.append("validation")
            return original_validate(records)

        def mock_persist(self, records):
            completed_stages.append("persistence")

        with patch.object(runner_mod, "validate_batch", mock_validate), \
             patch.object(runner_mod.PersistenceManager, "persist_records", mock_persist):
            run_pipeline(self.csv_path, self.config)

        self.assertIn("validation", completed_stages)
        self.assertIn("persistence", completed_stages)
        self.assertLess(
            completed_stages.index("validation"),
            completed_stages.index("persistence"),
        )

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    def test_pipeline_handles_missing_source_file(self):
        summary = run_pipeline("/nonexistent/path/data.csv")
        self.assertEqual(summary["status"], "failed")
        self.assertTrue(len(summary["errors"]) > 0)

    def test_pipeline_returns_summary_on_failure(self):
        """run_pipeline must always return a summary dict, even on failure."""
        summary = run_pipeline("/nonexistent/path/data.csv")
        self.assertIsInstance(summary, dict)
        self.assertIn("status", summary)
        self.assertIn("ended_at", summary)

    def test_pipeline_persists_adapted_records(self):
        """persist_records should be called with the adapted canonical records."""
        with patch(
            "modules.pipeline.runner.PersistenceManager.persist_records"
        ) as mock_persist:
            mock_persist.return_value = None
            summary = run_pipeline(self.csv_path, self.config)

        mock_persist.assert_called_once()
        persisted = mock_persist.call_args[0][0]
        self.assertEqual(len(persisted), summary["records_persisted"])


if __name__ == "__main__":
    unittest.main()
