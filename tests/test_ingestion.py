import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
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

from modules.ingestion.ingestion import ingest_data


class TestIngestionRouting(unittest.TestCase):
    def test_explicit_blob_style_source_path_routes_to_blob_loader(self):
        runtime_config = SimpleNamespace(
            blob_account="stopsightdev",
            azure_storage_connection_string=None,
        )
        expected_df = MagicMock(name="blob_dataframe")

        with patch("modules.ingestion.ingestion._get_runtime_config", return_value=runtime_config), \
            patch("modules.ingestion.ingestion._load_from_blob", return_value=expected_df) as mocked_blob_loader, \
            patch("modules.ingestion.ingestion._load_local_file") as mocked_local_loader:

            result = ingest_data(source_path="opsight-raw/csv/opsight_sample_sales.csv")

        self.assertIs(result, expected_df)
        mocked_blob_loader.assert_called_once_with(
            blob_account="stopsightdev",
            blob_container="opsight-raw",
            blob_path="csv/opsight_sample_sales.csv",
            connection_string=None,
        )
        mocked_local_loader.assert_not_called()

    def test_explicit_blob_style_source_path_routes_to_blob_loader_with_connection_string_only(self):
        runtime_config = SimpleNamespace(
            blob_account=None,
            azure_storage_connection_string="UseDevelopmentStorage=true",
        )
        expected_df = MagicMock(name="blob_dataframe")

        with patch("modules.ingestion.ingestion._get_runtime_config", return_value=runtime_config), \
            patch("modules.ingestion.ingestion._load_from_blob", return_value=expected_df) as mocked_blob_loader, \
            patch("modules.ingestion.ingestion._load_local_file") as mocked_local_loader:

            result = ingest_data(source_path="opsight-raw/csv/opsight_sample_sales.csv")

        self.assertIs(result, expected_df)
        mocked_blob_loader.assert_called_once_with(
            blob_account=None,
            blob_container="opsight-raw",
            blob_path="csv/opsight_sample_sales.csv",
            connection_string="UseDevelopmentStorage=true",
        )
        mocked_local_loader.assert_not_called()


if __name__ == "__main__":
    unittest.main()
