"""
Tests for XLSX dependency and loader availability.
Verifies that openpyxl is available and xlsx reading works.
"""

import sys
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from modules.ingestion.blob_client import BlobClient


class TestXlsxDependency(unittest.TestCase):
    """Verify openpyxl dependency and XLSX loader availability"""

    def test_openpyxl_is_importable(self):
        """openpyxl should be installed as a dependency."""
        try:
            import openpyxl
            self.assertIsNotNone(openpyxl)
        except ImportError:
            self.fail("openpyxl is not installed but is required for XLSX support")

    def test_pandas_read_excel_works(self):
        """Verify pd.read_excel can load XLSX data."""
        # Create a simple Excel file in memory
        df_original = pd.DataFrame({"name": ["Alice", "Bob"], "age": [30, 25]})
        
        # Write to BytesIO
        with BytesIO() as buffer:
            df_original.to_excel(buffer, index=False, engine='openpyxl')
            buffer.seek(0)
            excel_bytes = buffer.getvalue()

        # Read it back
        df_loaded = pd.read_excel(BytesIO(excel_bytes), engine='openpyxl')

        self.assertEqual(len(df_loaded), 2)
        self.assertListEqual(list(df_loaded.columns), ["name", "age"])

    @patch("modules.ingestion.blob_client.BlobServiceClient")
    def test_blob_client_reads_xlsx_format(self, mock_blob_service_class):
        """Verify BlobClient can read XLSX format from blob."""
        mock_service = Mock()
        mock_blob_service_class.return_value = mock_service

        mock_container = Mock()
        mock_service.get_container_client.return_value = mock_container

        mock_blob = Mock()
        mock_container.get_blob_client.return_value = mock_blob

        # Create XLSX bytes
        df_original = pd.DataFrame({"product": ["Widget", "Gadget"], "price": [10.0, 20.0]})
        with BytesIO() as buffer:
            df_original.to_excel(buffer, index=False, engine='openpyxl')
            buffer.seek(0)
            xlsx_bytes = buffer.getvalue()

        mock_stream = Mock()
        mock_stream.readall.return_value = xlsx_bytes
        mock_blob.download_blob.return_value = mock_stream

        with patch("modules.ingestion.blob_client.DefaultAzureCredential"):
            client = BlobClient(
                blob_account="myaccount",
                blob_container="mycontainer",
                blob_path="data.xlsx",
            )

            result = client.read_blob_data(data_format="xlsx")

            assert result["status"] == "success"
            assert len(result["rows"]) == 2
            assert list(result["rows"].columns) == ["product", "price"]
            assert result["source"] == "blob"


if __name__ == "__main__":
    unittest.main()
