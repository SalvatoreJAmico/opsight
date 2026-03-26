import os
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pandas as pd

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

from modules.ingestion.csv_reader import CsvDecodingError, read_csv_with_fallback
from modules.ingestion.ingestion import ingest_data, load_source


class TestCsvDecodingFallback(unittest.TestCase):
    def test_read_csv_with_fallback_retries_cp1252_after_utf8_failure(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / "cp1252-data.csv"
            csv_path.write_bytes("name\nA\xa0B\n".encode("cp1252"))

            dataframe = read_csv_with_fallback(csv_path)

        self.assertEqual(list(dataframe.columns), ["name"])
        self.assertEqual(dataframe.iloc[0]["name"], "A\xa0B")

    def test_read_csv_with_fallback_raises_clear_error_after_all_attempts(self):
        decode_error = UnicodeDecodeError("utf-8", b"\xa0", 0, 1, "invalid start byte")

        with patch("modules.ingestion.csv_reader.pd.read_csv", side_effect=[decode_error, decode_error, decode_error]):
            with self.assertRaises(CsvDecodingError) as raised:
                read_csv_with_fallback("broken.csv")

        self.assertIn("utf-8, cp1252, latin-1", str(raised.exception))

    def test_load_source_csv_uses_shared_csv_fallback(self):
        expected = pd.DataFrame([{"value": 1}])

        with patch("modules.ingestion.ingestion.read_csv_with_fallback", return_value=expected) as mocked_reader:
            result = load_source("sample.csv", "csv")

        pd.testing.assert_frame_equal(result, expected)
        mocked_reader.assert_called_once_with("sample.csv")


class TestSourceNormalization(unittest.TestCase):
    def test_load_source_json_flattens_nested_transactions_payload(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_path = Path(tmp_dir) / "mock-transactions.json"
            source_path.write_text(
                json.dumps(
                    {
                        "transactions": [
                            {"id": "TXN-001", "date": "2024-01-01", "amount": 25.0}
                        ]
                    }
                ),
                encoding="utf-8",
            )

            dataframe = load_source(str(source_path), "json")

        self.assertIn("id", dataframe.columns)
        self.assertIn("date", dataframe.columns)
        self.assertEqual(dataframe.iloc[0]["id"], "TXN-001")

    def test_load_source_excel_promotes_embedded_header_row(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_path = Path(tmp_dir) / "Employee-Management-Sample-Data.xlsx"

            pd.DataFrame(
                {
                    "Unnamed: 0": [None, None, None, None],
                    "Unnamed: 1": ["Employee Management Data", None, "Employee ID", "S1001"],
                    "Unnamed: 2": [None, None, "Full Name", "John Smith"],
                    "Unnamed: 3": [None, None, "Hire Date", pd.Timestamp("2023-05-15")],
                }
            ).to_excel(source_path, index=False)

            dataframe = load_source(str(source_path), "excel")

        self.assertEqual(list(dataframe.columns)[0], "Employee ID")
        self.assertIn("Hire Date", dataframe.columns)
        self.assertEqual(dataframe.iloc[0]["Employee ID"], "S1001")


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
            data_format=None,
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
            data_format=None,
        )
        mocked_local_loader.assert_not_called()


if __name__ == "__main__":
    unittest.main()
