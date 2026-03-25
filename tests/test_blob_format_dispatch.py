"""
Tests for format-aware blob data reading
Tests the new read_blob_data function that dispatches by format
"""

import io
import pytest
from unittest.mock import Mock, patch, MagicMock

import pandas as pd
from azure.core.exceptions import (
    ClientAuthenticationError,
    ResourceNotFoundError,
)

from modules.ingestion.blob_client import (
    BlobClient,
    BlobAuthenticationError,
    BlobNotFoundError,
    BlobNetworkError,
    read_blob_data,
)


class TestBlobClientFormatAwareReading:
    """Test BlobClient.read_blob_data() for format-aware reading"""

    @patch("modules.ingestion.blob_client.BlobServiceClient")
    def test_read_blob_data_csv_format(self, mock_blob_service_class):
        """Should read CSV format from blob."""
        mock_service = Mock()
        mock_blob_service_class.return_value = mock_service

        mock_container = Mock()
        mock_service.get_container_client.return_value = mock_container

        mock_blob = Mock()
        mock_container.get_blob_client.return_value = mock_blob

        # Simulate CSV blob
        csv_data = b"col1,col2\n1,2\n3,4"
        mock_stream = Mock()
        mock_stream.readall.return_value = csv_data
        mock_blob.download_blob.return_value = mock_stream

        with patch("modules.ingestion.blob_client.DefaultAzureCredential"):
            with patch("modules.ingestion.blob_client.read_csv_with_fallback") as mock_csv_reader:
                mock_csv_reader.return_value = pd.DataFrame({"col1": [1, 3], "col2": [2, 4]})
                
                client = BlobClient(
                    blob_account="myaccount",
                    blob_container="mycontainer",
                    blob_path="data.csv",
                )

                result = client.read_blob_data(data_format="csv")

                assert result["status"] == "success"
                assert isinstance(result["rows"], pd.DataFrame)
                assert result["source"] == "blob"
                mock_csv_reader.assert_called_once()

    @patch("modules.ingestion.blob_client.BlobServiceClient")
    @patch("pandas.read_json")
    def test_read_blob_data_json_format(self, mock_read_json, mock_blob_service_class):
        """Should read JSON format from blob."""
        mock_service = Mock()
        mock_blob_service_class.return_value = mock_service

        mock_container = Mock()
        mock_service.get_container_client.return_value = mock_container

        mock_blob = Mock()
        mock_container.get_blob_client.return_value = mock_blob

        # Simulate JSON blob
        json_data = b'[{"id": 1}, {"id": 2}]'
        mock_stream = Mock()
        mock_stream.readall.return_value = json_data
        mock_blob.download_blob.return_value = mock_stream

        expected_df = pd.DataFrame({"id": [1, 2]})
        mock_read_json.return_value = expected_df

        with patch("modules.ingestion.blob_client.DefaultAzureCredential"):
            client = BlobClient(
                blob_account="myaccount",
                blob_container="mycontainer",
                blob_path="data.json",
            )

            result = client.read_blob_data(data_format="json")

            assert result["status"] == "success"
            assert result["rows"] is expected_df
            assert result["source"] == "blob"
            mock_read_json.assert_called_once()

    @patch("modules.ingestion.blob_client.BlobServiceClient")
    @patch("pandas.read_json")
    def test_read_blob_data_json_flattens_single_object_column(self, mock_read_json, mock_blob_service_class):
        mock_service = Mock()
        mock_blob_service_class.return_value = mock_service

        mock_container = Mock()
        mock_service.get_container_client.return_value = mock_container

        mock_blob = Mock()
        mock_container.get_blob_client.return_value = mock_blob

        mock_stream = Mock()
        mock_stream.readall.return_value = b'{"transactions": []}'
        mock_blob.download_blob.return_value = mock_stream
        mock_read_json.return_value = pd.DataFrame(
            {"transactions": [{"id": "TXN-001", "date": "2024-01-01", "amount": 25.0}]}
        )

        with patch("modules.ingestion.blob_client.DefaultAzureCredential"):
            client = BlobClient(
                blob_account="myaccount",
                blob_container="mycontainer",
                blob_path="data.json",
            )

            result = client.read_blob_data(data_format="json")

        assert list(result["rows"].columns) == ["id", "date", "amount"]
        assert result["rows"].iloc[0]["id"] == "TXN-001"

    @patch("modules.ingestion.blob_client.BlobServiceClient")
    @patch("pandas.read_parquet")
    def test_read_blob_data_parquet_format(self, mock_read_parquet, mock_blob_service_class):
        """Should read Parquet format from blob."""
        mock_service = Mock()
        mock_blob_service_class.return_value = mock_service

        mock_container = Mock()
        mock_service.get_container_client.return_value = mock_container

        mock_blob = Mock()
        mock_container.get_blob_client.return_value = mock_blob

        # Simulate Parquet blob (just bytes)
        parquet_data = b"PAR1..." # Simplified
        mock_stream = Mock()
        mock_stream.readall.return_value = parquet_data
        mock_blob.download_blob.return_value = mock_stream

        expected_df = pd.DataFrame({"col": [1, 2, 3]})
        mock_read_parquet.return_value = expected_df

        with patch("modules.ingestion.blob_client.DefaultAzureCredential"):
            client = BlobClient(
                blob_account="myaccount",
                blob_container="mycontainer",
                blob_path="data.parquet",
            )

            result = client.read_blob_data(data_format="parquet")

            assert result["status"] == "success"
            assert result["rows"] is expected_df
            assert result["source"] == "blob"
            mock_read_parquet.assert_called_once()

    @patch("modules.ingestion.blob_client.BlobServiceClient")
    @patch("pandas.read_excel")
    def test_read_blob_data_excel_format(self, mock_read_excel, mock_blob_service_class):
        """Should read Excel format from blob."""
        mock_service = Mock()
        mock_blob_service_class.return_value = mock_service

        mock_container = Mock()
        mock_service.get_container_client.return_value = mock_container

        mock_blob = Mock()
        mock_container.get_blob_client.return_value = mock_blob

        # Simulate Excel blob
        excel_data = b"PK..." # Simplified ZIP-like header
        mock_stream = Mock()
        mock_stream.readall.return_value = excel_data
        mock_blob.download_blob.return_value = mock_stream

        expected_df = pd.DataFrame({"col": [1, 2, 3]})
        mock_read_excel.return_value = expected_df

        with patch("modules.ingestion.blob_client.DefaultAzureCredential"):
            client = BlobClient(
                blob_account="myaccount",
                blob_container="mycontainer",
                blob_path="data.xlsx",
            )

            result = client.read_blob_data(data_format="xlsx")

            assert result["status"] == "success"
            assert result["rows"] is expected_df
            assert result["source"] == "blob"
            mock_read_excel.assert_called_once()

    @patch("modules.ingestion.blob_client.BlobServiceClient")
    @patch("pandas.read_excel")
    def test_read_blob_data_excel_promotes_embedded_header_row(self, mock_read_excel, mock_blob_service_class):
        mock_service = Mock()
        mock_blob_service_class.return_value = mock_service

        mock_container = Mock()
        mock_service.get_container_client.return_value = mock_container

        mock_blob = Mock()
        mock_container.get_blob_client.return_value = mock_blob

        mock_stream = Mock()
        mock_stream.readall.return_value = b"PK..."
        mock_blob.download_blob.return_value = mock_stream
        mock_read_excel.return_value = pd.DataFrame(
            {
                "Unnamed: 0": [None, None, None, None],
                "Unnamed: 1": ["Employee Management Data", None, "Employee ID", "S1001"],
                "Unnamed: 2": [None, None, "Full Name", "John Smith"],
                "Unnamed: 3": [None, None, "Hire Date", pd.Timestamp("2023-05-15")],
            }
        )

        with patch("modules.ingestion.blob_client.DefaultAzureCredential"):
            client = BlobClient(
                blob_account="myaccount",
                blob_container="mycontainer",
                blob_path="data.xlsx",
            )

            result = client.read_blob_data(data_format="xlsx")

        assert list(result["rows"].columns) == ["Employee ID", "Full Name", "Hire Date"]
        assert result["rows"].iloc[0]["Employee ID"] == "S1001"

    @patch("modules.ingestion.blob_client.BlobServiceClient")
    def test_read_blob_data_detects_format_from_extension(self, mock_blob_service_class):
        """Should detect format from blob_path extension if not specified."""
        mock_service = Mock()
        mock_blob_service_class.return_value = mock_service

        mock_container = Mock()
        mock_service.get_container_client.return_value = mock_container

        mock_blob = Mock()
        mock_container.get_blob_client.return_value = mock_blob

        # Simulate JSON blob
        json_data = b'[{"id": 1}]'
        mock_stream = Mock()
        mock_stream.readall.return_value = json_data
        mock_blob.download_blob.return_value = mock_stream

        with patch("modules.ingestion.blob_client.DefaultAzureCredential"):
            with patch("pandas.read_json") as mock_read_json:
                mock_read_json.return_value = pd.DataFrame({"id": [1]})
                
                client = BlobClient(
                    blob_account="myaccount",
                    blob_container="mycontainer",
                    blob_path="data.json",
                )

                # Call without format - should auto-detect from .json extension
                result = client.read_blob_data()

                assert result["status"] == "success"
                mock_read_json.assert_called_once()

    @patch("modules.ingestion.blob_client.BlobServiceClient")
    def test_read_blob_data_defaults_to_csv_if_no_format_detected(self, mock_blob_service_class):
        """Should default to CSV if format cannot be detected."""
        mock_service = Mock()
        mock_blob_service_class.return_value = mock_service

        mock_container = Mock()
        mock_service.get_container_client.return_value = mock_container

        mock_blob = Mock()
        mock_container.get_blob_client.return_value = mock_blob

        # Simulate CSV blob
        csv_data = b"col1,col2\n1,2"
        mock_stream = Mock()
        mock_stream.readall.return_value = csv_data
        mock_blob.download_blob.return_value = mock_stream

        with patch("modules.ingestion.blob_client.DefaultAzureCredential"):
            with patch("modules.ingestion.blob_client.read_csv_with_fallback") as mock_csv_reader:
                mock_csv_reader.return_value = pd.DataFrame({"col1": [1], "col2": [2]})
                
                client = BlobClient(
                    blob_account="myaccount",
                    blob_container="mycontainer",
                    blob_path="data",  # No extension - should default to CSV
                )

                result = client.read_blob_data()

                assert result["status"] == "success"
                mock_csv_reader.assert_called_once()

    @patch("modules.ingestion.blob_client.BlobServiceClient")
    def test_read_blob_data_unsupported_format_raises_error(self, mock_blob_service_class):
        """Should raise ValueError for unsupported format."""
        mock_service = Mock()
        mock_blob_service_class.return_value = mock_service

        mock_container = Mock()
        mock_service.get_container_client.return_value = mock_container

        mock_blob = Mock()
        mock_container.get_blob_client.return_value = mock_blob

        mock_stream = Mock()
        mock_stream.readall.return_value = b"some data"
        mock_blob.download_blob.return_value = mock_stream

        with patch("modules.ingestion.blob_client.DefaultAzureCredential"):
            client = BlobClient(
                blob_account="myaccount",
                blob_container="mycontainer",
                blob_path="data.xyz",
            )

            with pytest.raises(ValueError, match="Unsupported blob format: unsupported"):
                client.read_blob_data(data_format="unsupported")


class TestReadBlobDataFunction:
    """Test the convenience function read_blob_data()"""

    @patch("modules.ingestion.blob_client.BlobClient.read_blob_data")
    def test_read_blob_data_function_with_format(self, mock_read):
        """Should create client and call read_blob_data with format."""
        mock_result = {
            "status": "success",
            "rows": pd.DataFrame({"id": [1, 2]}),
            "source": "blob",
        }
        mock_read.return_value = mock_result

        result = read_blob_data(
            blob_account="myaccount",
            blob_container="mycontainer",
            blob_path="data.json",
            data_format="json",
        )

        assert result is mock_result
        mock_read.assert_called_once_with(data_format="json")

    @patch("modules.ingestion.blob_client.BlobClient.read_blob_data")
    def test_read_blob_data_function_without_format(self, mock_read):
        """Should call read_blob_data without format to trigger auto-detection."""
        mock_result = {
            "status": "success",
            "rows": pd.DataFrame({"col": [1]}),
            "source": "blob",
        }
        mock_read.return_value = mock_result

        result = read_blob_data(
            blob_account="myaccount",
            blob_container="mycontainer",
            blob_path="data.csv",
        )

        assert result is mock_result
        mock_read.assert_called_once_with(data_format=None)
