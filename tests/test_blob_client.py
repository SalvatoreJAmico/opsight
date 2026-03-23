"""
Tests for blob_client.py
PS-094: Blob access with proper error handling

Coverage:
- Managed identity initialization
- Connection string initialization
- Successful CSV reads
- Authentication errors
- Not found errors (blob and container)
- Network errors
"""

import io
import pytest
from unittest.mock import Mock, patch, MagicMock

import pandas as pd
from azure.core.exceptions import (
    ClientAuthenticationError,
    ResourceNotFoundError,
    ServiceRequestError,
    HttpResponseError,
)

from modules.ingestion.blob_client import (
    BlobClient,
    BlobAuthenticationError,
    BlobNotFoundError,
    BlobNetworkError,
    read_blob_csv,
)


class TestBlobClientInitialization:
    """Test BlobClient initialization and validation"""

    def test_init_with_valid_params(self):
        """Should initialize with valid parameters."""
        client = BlobClient(
            blob_account="myaccount",
            blob_container="mycontainer",
            blob_path="data/file.csv",
        )
        assert client.blob_account == "myaccount"
        assert client.blob_container == "mycontainer"
        assert client.blob_path == "data/file.csv"
        assert client._auth_method == "managed_identity"

    def test_init_with_connection_string(self):
        """Should initialize with connection string auth method."""
        client = BlobClient(
            blob_account="myaccount",
            blob_container="mycontainer",
            blob_path="data/file.csv",
            connection_string="DefaultEndpointsProtocol=https;...",
        )
        assert client._auth_method == "connection_string"
        assert client.connection_string == "DefaultEndpointsProtocol=https;..."

    def test_init_empty_account_raises_error(self):
        """Should raise ValueError if blob_account is empty without connection string."""
        with pytest.raises(ValueError, match="blob_account cannot be empty when connection_string is not provided"):
            BlobClient(
                blob_account="",
                blob_container="mycontainer",
                blob_path="file.csv",
            )

    def test_init_empty_account_with_connection_string_is_allowed(self):
        """Should allow empty blob_account when connection string is provided."""
        client = BlobClient(
            blob_account="",
            blob_container="mycontainer",
            blob_path="file.csv",
            connection_string="DefaultEndpointsProtocol=https;...",
        )
        assert client.blob_account == ""
        assert client._auth_method == "connection_string"

    def test_init_empty_container_raises_error(self):
        """Should raise ValueError if blob_container is empty."""
        with pytest.raises(ValueError, match="blob_container cannot be empty"):
            BlobClient(
                blob_account="myaccount",
                blob_container="",
                blob_path="file.csv",
            )

    def test_init_empty_path_raises_error(self):
        """Should raise ValueError if blob_path is empty."""
        with pytest.raises(ValueError, match="blob_path cannot be empty"):
            BlobClient(
                blob_account="myaccount",
                blob_container="mycontainer",
                blob_path="",
            )

    def test_init_whitespace_params_are_stripped(self):
        """Should strip whitespace from params."""
        client = BlobClient(
            blob_account="  myaccount  ",
            blob_container="  mycontainer  ",
            blob_path="  data/file.csv  ",
        )
        assert client.blob_account == "myaccount"
        assert client.blob_container == "mycontainer"
        assert client.blob_path == "data/file.csv"


class TestBlobClientAuthenticatin:
    """Test authentication path initialization"""

    @patch("modules.ingestion.blob_client.BlobServiceClient.from_connection_string")
    def test_connection_string_auth_success(self, mock_from_conn_str):
        """Should initialize with connection string successfully."""
        mock_service = Mock()
        mock_from_conn_str.return_value = mock_service

        client = BlobClient(
            blob_account="myaccount",
            blob_container="mycontainer",
            blob_path="file.csv",
            connection_string="connection_string_value",
        )
        service = client._get_service_client()

        assert service == mock_service
        mock_from_conn_str.assert_called_once_with("connection_string_value")

    @patch("modules.ingestion.blob_client.DefaultAzureCredential")
    @patch("modules.ingestion.blob_client.BlobServiceClient")
    def test_managed_identity_auth_success(self, mock_blob_service_class, mock_credential):
        """Should initialize with managed identity successfully."""
        mock_credential_instance = Mock()
        mock_credential.return_value = mock_credential_instance
        mock_service = Mock()
        mock_blob_service_class.return_value = mock_service

        client = BlobClient(
            blob_account="myaccount",
            blob_container="mycontainer",
            blob_path="file.csv",
        )
        service = client._get_service_client()

        assert service == mock_service
        expected_url = "https://myaccount.blob.core.windows.net"
        mock_blob_service_class.assert_called_once()
        call_args = mock_blob_service_class.call_args
        assert call_args[1]["account_url"] == expected_url
        assert call_args[1]["credential"] == mock_credential_instance

    @patch("modules.ingestion.blob_client.BlobServiceClient.from_connection_string")
    def test_connection_string_auth_failure(self, mock_from_conn_str):
        """Should raise BlobAuthenticationError on connection string auth failure."""
        mock_from_conn_str.side_effect = ClientAuthenticationError("Invalid connection string")

        client = BlobClient(
            blob_account="myaccount",
            blob_container="mycontainer",
            blob_path="file.csv",
            connection_string="invalid_string",
        )

        with pytest.raises(
            BlobAuthenticationError,
            match="Failed to authenticate with Blob Storage.*connection_string",
        ):
            client._get_service_client()

    @patch("modules.ingestion.blob_client.DefaultAzureCredential")
    def test_managed_identity_auth_failure(self, mock_credential):
        """Should raise BlobAuthenticationError on managed identity auth failure."""
        mock_credential.side_effect = ClientAuthenticationError("No credentials found")

        client = BlobClient(
            blob_account="myaccount",
            blob_container="mycontainer",
            blob_path="file.csv",
        )

        with pytest.raises(
            BlobAuthenticationError,
            match="Failed to authenticate with Blob Storage.*managed_identity",
        ):
            client._get_service_client()


class TestBlobClientReadCSV:
    """Test read_blob_csv functionality"""

    @patch("modules.ingestion.blob_client.BlobServiceClient")
    def test_read_blob_csv_success(self, mock_blob_service_class):
        """Should successfully read and parse CSV from blob."""
        # Setup mock blob service chain
        mock_service = Mock()
        mock_blob_service_class.return_value = mock_service

        mock_container = Mock()
        mock_service.get_container_client.return_value = mock_container

        mock_blob = Mock()
        mock_container.get_blob_client.return_value = mock_blob

        # Create sample CSV data
        csv_data = "name,age\nAlice,30\nBob,25"
        mock_download = Mock()
        mock_download.readall.return_value = csv_data.encode()
        mock_blob.download_blob.return_value = mock_download

        # Mock DefaultAzureCredential
        with patch("modules.ingestion.blob_client.DefaultAzureCredential"):
            client = BlobClient(
                blob_account="myaccount",
                blob_container="mycontainer",
                blob_path="data.csv",
            )
            result = client.read_blob_csv()

        assert result["status"] == "success"
        assert result["source"] == "blob"
        assert isinstance(result["rows"], pd.DataFrame)
        assert list(result["rows"].columns) == ["name", "age"]
        assert len(result["rows"]) == 2
        assert result["rows"].iloc[0]["name"] == "Alice"

    @patch("modules.ingestion.blob_client.BlobServiceClient")
    def test_read_blob_csv_authentication_error(self, mock_blob_service_class):
        """Should raise BlobAuthenticationError on auth failure."""
        mock_service = Mock()
        mock_blob_service_class.return_value = mock_service

        mock_container = Mock()
        mock_service.get_container_client.return_value = mock_container

        mock_blob = Mock()
        mock_container.get_blob_client.return_value = mock_blob

        # Simulate auth error
        mock_blob.download_blob.side_effect = ClientAuthenticationError("No permission")

        with patch("modules.ingestion.blob_client.DefaultAzureCredential"):
            client = BlobClient(
                blob_account="myaccount",
                blob_container="mycontainer",
                blob_path="data.csv",
            )

            with pytest.raises(
                BlobAuthenticationError,
                match="Authentication/authorization failed",
            ):
                client.read_blob_csv()

    @patch("modules.ingestion.blob_client.BlobServiceClient")
    def test_read_blob_csv_container_not_found(self, mock_blob_service_class):
        """Should raise BlobNotFoundError when container not found."""
        mock_service = Mock()
        mock_blob_service_class.return_value = mock_service

        mock_container = Mock()
        mock_service.get_container_client.return_value = mock_container

        mock_blob = Mock()
        mock_container.get_blob_client.return_value = mock_blob

        # Simulate container not found
        error = ResourceNotFoundError("ContainerNotFound")
        mock_blob.download_blob.side_effect = error

        with patch("modules.ingestion.blob_client.DefaultAzureCredential"):
            client = BlobClient(
                blob_account="myaccount",
                blob_container="missing",
                blob_path="data.csv",
            )

            with pytest.raises(
                BlobNotFoundError,
                match="Container 'missing' not found",
            ):
                client.read_blob_csv()

    @patch("modules.ingestion.blob_client.BlobServiceClient")
    def test_read_blob_csv_blob_not_found(self, mock_blob_service_class):
        """Should raise BlobNotFoundError when blob not found."""
        mock_service = Mock()
        mock_blob_service_class.return_value = mock_service

        mock_container = Mock()
        mock_service.get_container_client.return_value = mock_container

        mock_blob = Mock()
        mock_container.get_blob_client.return_value = mock_blob

        # Simulate blob not found
        error = ResourceNotFoundError("BlobNotFound")
        mock_blob.download_blob.side_effect = error

        with patch("modules.ingestion.blob_client.DefaultAzureCredential"):
            client = BlobClient(
                blob_account="myaccount",
                blob_container="mycontainer",
                blob_path="missing.csv",
            )

            with pytest.raises(
                BlobNotFoundError,
                match="Blob 'missing.csv' not found",
            ):
                client.read_blob_csv()

    @patch("modules.ingestion.blob_client.BlobServiceClient")
    def test_read_blob_csv_network_error(self, mock_blob_service_class):
        """Should raise BlobNetworkError on network issues."""
        mock_service = Mock()
        mock_blob_service_class.return_value = mock_service

        mock_container = Mock()
        mock_service.get_container_client.return_value = mock_container

        mock_blob = Mock()
        mock_container.get_blob_client.return_value = mock_blob

        # Simulate service error
        error = ServiceRequestError("Connection timeout")
        mock_blob.download_blob.side_effect = error

        with patch("modules.ingestion.blob_client.DefaultAzureCredential"):
            client = BlobClient(
                blob_account="myaccount",
                blob_container="mycontainer",
                blob_path="data.csv",
            )

            with pytest.raises(
                BlobNetworkError,
                match="Network error accessing Blob Storage",
            ):
                client.read_blob_csv()

    @patch("modules.ingestion.blob_client.BlobServiceClient")
    def test_read_blob_csv_http_response_error(self, mock_blob_service_class):
        """Should raise BlobNetworkError on HTTP response errors."""
        mock_service = Mock()
        mock_blob_service_class.return_value = mock_service

        mock_container = Mock()
        mock_service.get_container_client.return_value = mock_container

        mock_blob = Mock()
        mock_container.get_blob_client.return_value = mock_blob

        # Simulate HTTP error
        error = HttpResponseError("Internal Server Error")
        mock_blob.download_blob.side_effect = error

        with patch("modules.ingestion.blob_client.DefaultAzureCredential"):
            client = BlobClient(
                blob_account="myaccount",
                blob_container="mycontainer",
                blob_path="data.csv",
            )

            with pytest.raises(
                BlobNetworkError,
                match="Network error accessing Blob Storage",
            ):
                client.read_blob_csv()


class TestReadBlobCSVFunction:
    """Test the convenience function read_blob_csv()"""

    @patch("modules.ingestion.blob_client.BlobClient.read_blob_csv")
    def test_read_blob_csv_function(self, mock_read):
        """Should create client and call read_blob_csv."""
        mock_result = {
            "status": "success",
            "rows": pd.DataFrame({"col": [1, 2, 3]}),
            "source": "blob",
        }
        mock_read.return_value = mock_result

        result = read_blob_csv(
            blob_account="myaccount",
            blob_container="mycontainer",
            blob_path="data.csv",
        )

        assert result is mock_result
        mock_read.assert_called_once()

    @patch("modules.ingestion.blob_client.BlobClient.read_blob_csv")
    def test_read_blob_csv_function_with_connection_string(self, mock_read):
        """Should pass connection string to client."""
        mock_result = {
            "status": "success",
            "rows": pd.DataFrame({"col": [1, 2, 3]}),
            "source": "blob",
        }
        mock_read.return_value = mock_result

        result = read_blob_csv(
            blob_account="myaccount",
            blob_container="mycontainer",
            blob_path="data.csv",
            connection_string="conn_str",
        )

        assert result is mock_result
        mock_read.assert_called_once()
