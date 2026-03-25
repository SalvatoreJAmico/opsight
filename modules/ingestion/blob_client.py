"""
Blob Storage Client for Opsight Ingestion
PS-094: Centralized Blob access with clear auth/network/notfound error handling

Supports two auth paths:
- Managed identity (production preferred)
- Connection string (transitional/local fallback only)

Error categories:
- BlobAuthenticationError: auth/permission failures
- BlobNotFoundError: missing blob/container
- BlobNetworkError: connectivity issues
"""

import io
import logging
from typing import Any, Dict, Optional
from enum import Enum

import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.core.exceptions import (
    ClientAuthenticationError,
    ResourceNotFoundError,
    ServiceRequestError,
    HttpResponseError,
)
from modules.ingestion.csv_reader import CsvDecodingError, read_csv_with_fallback
from modules.ingestion.dataframe_normalizer import normalize_loaded_dataframe

logger = logging.getLogger("opsight.ingestion.blob")


class BlobErrorCategory(Enum):
    """Categories of Blob access errors"""
    AUTHENTICATION = "auth"
    NOT_FOUND = "not_found"
    NETWORK = "network"
    UNKNOWN = "unknown"


class BlobAuthenticationError(Exception):
    """
    Raised when Blob authentication or authorization fails.
    Examples: invalid credentials, no role assignment, identity cannot access container.
    """
    def __init__(self, message: str, details: Optional[str] = None):
        full_msg = f"Blob authentication failed: {message}"
        if details:
            full_msg += f" ({details})"
        super().__init__(full_msg)


class BlobNotFoundError(Exception):
    """
    Raised when Blob or container is not found.
    Examples: blob path wrong, container wrong, file not found.
    """
    def __init__(self, message: str, details: Optional[str] = None):
        full_msg = f"Blob not found: {message}"
        if details:
            full_msg += f" ({details})"
        super().__init__(full_msg)


class BlobNetworkError(Exception):
    """
    Raised when network connectivity issue occurs.
    Examples: DNS failure, timeout, storage endpoint unavailable.
    """
    def __init__(self, message: str, details: Optional[str] = None):
        full_msg = f"Blob network error: {message}"
        if details:
            full_msg += f" ({details})"
        super().__init__(full_msg)


class BlobClient:
    """
    Centralized Blob Storage access layer.
    Handles both managed identity and connection string auth paths.
    Routes requests through configuration to enforce dev/prod rules.
    """

    def __init__(
        self,
        blob_account: Optional[str],
        blob_container: str,
        blob_path: str,
        connection_string: Optional[str] = None,
    ):
        """
        Initialize BlobClient.

        Args:
            blob_account: Storage account name (e.g., "mystorageaccount")
            blob_container: Container name (e.g., "data")
            blob_path: Path within container (e.g., "input.csv")
            connection_string: Optional connection string for transitional auth.
                              If None, uses managed identity via DefaultAzureCredential.

        Raises:
            ValueError: If required parameters are missing or invalid.
        """
        if (not blob_account or not str(blob_account).strip()) and not connection_string:
            raise ValueError("blob_account cannot be empty when connection_string is not provided")
        if not blob_container or not blob_container.strip():
            raise ValueError("blob_container cannot be empty")
        if not blob_path or not blob_path.strip():
            raise ValueError("blob_path cannot be empty")

        self.blob_account = (blob_account or "").strip()
        self.blob_container = blob_container.strip()
        self.blob_path = blob_path.strip()
        self.connection_string = connection_string

        self._service_client = None
        self._auth_method = "connection_string" if connection_string else "managed_identity"

    def _get_service_client(self) -> object:
        """
        Lazily initialize and return the BlobServiceClient.
        Supports both managed identity and connection string auth.

        Returns:
            BlobServiceClient instance

        Raises:
            BlobAuthenticationError: If client initialization fails.
        """
        if self._service_client is not None:
            return self._service_client

        try:
            if self.connection_string:
                logger.debug(
                    "Initializing BlobServiceClient with connection string",
                    extra={
                        "event": "blob_client_initialization",
                        "source": "blob",
                        "status": "started",
                    },
                )
                self._service_client = BlobServiceClient.from_connection_string(
                    self.connection_string
                )
            else:
                logger.debug(
                    "Initializing BlobServiceClient with managed identity",
                    extra={
                        "event": "blob_client_initialization",
                        "source": "blob",
                        "status": "started",
                    },
                )
                credential = DefaultAzureCredential()
                account_url = f"https://{self.blob_account}.blob.core.windows.net"
                self._service_client = BlobServiceClient(
                    account_url=account_url,
                    credential=credential,
                )
            return self._service_client
        except ClientAuthenticationError as e:
            logger.error(
                "Blob authentication failed during client initialization",
                extra={
                    "event": "blob_authentication_failed",
                    "source": "blob",
                    "status": "failed",
                    "error_type": "blob_authentication_error",
                    "error_message": str(e),
                },
            )
            raise BlobAuthenticationError(
                f"Failed to authenticate with Blob Storage ({self._auth_method})",
                str(e),
            ) from e
        except Exception as e:
            logger.error(
                "Blob client initialization failed",
                extra={
                    "event": "blob_network_error",
                    "source": "blob",
                    "status": "failed",
                    "error_type": "blob_network_error",
                    "error_message": str(e),
                },
            )
            raise BlobAuthenticationError(
                f"Failed to initialize Blob Storage client ({self._auth_method})",
                str(e),
            ) from e

    def read_blob_csv(self) -> Dict[str, Any]:
        """
        Read blob content as CSV and return a structured payload.

        Returns:
            dict with status, rows (DataFrame), and source metadata

        Raises:
            BlobAuthenticationError: If auth/permission fails
            BlobNotFoundError: If blob/container not found
            BlobNetworkError: If connectivity issue occurs
        """
        try:
            service_client = self._get_service_client()
            container_client = service_client.get_container_client(self.blob_container)
            blob_client = container_client.get_blob_client(self.blob_path)

            logger.info(
                "Blob read started",
                extra={
                    "event": "blob_read_started",
                    "source": "blob",
                    "status": "started",
                },
            )

            # Download blob content into bytes buffer
            download_stream = blob_client.download_blob()
            blob_bytes = download_stream.readall()

            # Parse CSV from bytes into DataFrame
            df = read_csv_with_fallback(io.BytesIO(blob_bytes))
            logger.info(
                "Blob read completed",
                extra={
                    "event": "blob_read_completed",
                    "source": "blob",
                    "status": "success",
                },
            )
            return {
                "status": "success",
                "rows": df,
                "source": "blob",
            }

        except CsvDecodingError:
            raise

        except ClientAuthenticationError as e:
            error_msg = (
                f"Authentication/authorization failed for "
                f"account={self.blob_account}, container={self.blob_container}"
            )
            logger.error(
                error_msg,
                extra={
                    "event": "blob_authentication_failed",
                    "source": "blob",
                    "status": "failed",
                    "error_type": "blob_authentication_error",
                    "error_message": str(e),
                },
            )
            raise BlobAuthenticationError(error_msg, str(e)) from e

        except ResourceNotFoundError as e:
            # Distinguish between container not found and blob not found
            if "ContainerNotFound" in str(e):
                error_msg = f"Container '{self.blob_container}' not found"
            else:
                error_msg = f"Blob '{self.blob_path}' not found in container '{self.blob_container}'"
            logger.error(
                error_msg,
                extra={
                    "event": "blob_not_found",
                    "source": "blob",
                    "status": "failed",
                    "error_type": "blob_not_found_error",
                    "error_message": str(e),
                },
            )
            raise BlobNotFoundError(error_msg, str(e)) from e

        except (ServiceRequestError, HttpResponseError) as e:
            # Network-level errors or transient HTTP errors
            error_msg = (
                f"Network error accessing Blob Storage "
                f"(account={self.blob_account})"
            )
            logger.error(
                error_msg,
                extra={
                    "event": "blob_network_error",
                    "source": "blob",
                    "status": "failed",
                    "error_type": "blob_network_error",
                    "error_message": str(e),
                },
            )
            raise BlobNetworkError(error_msg, str(e)) from e

        except Exception as e:
            # Catch other potential errors and categorize as network
            error_msg = f"Unexpected error reading blob: {type(e).__name__}"
            logger.error(
                error_msg,
                extra={
                    "event": "blob_network_error",
                    "source": "blob",
                    "status": "failed",
                    "error_type": "blob_network_error",
                    "error_message": str(e),
                },
            )
            raise BlobNetworkError(error_msg, str(e)) from e

    def read_blob_data(self, data_format: Optional[str] = None) -> Dict[str, Any]:
        """
        Read blob content according to specified format and return a structured payload.

        Args:
            data_format: Format of the blob data (csv/json/parquet/xlsx)
                         If None, attempts to detect from blob_path extension

        Returns:
            dict with status, rows (DataFrame), and source metadata

        Raises:
            BlobAuthenticationError: If auth/permission fails
            BlobNotFoundError: If blob/container not found
            BlobNetworkError: If connectivity issue occurs
            ValueError: If format is unsupported
        """
        # Detect format from filename if not specified
        if not data_format:
            if self.blob_path.endswith(".json"):
                data_format = "json"
            elif self.blob_path.endswith(".parquet"):
                data_format = "parquet"
            elif self.blob_path.endswith((".xlsx", ".xlsm", ".xltx", ".xltm")):
                data_format = "xlsx"
            else:
                data_format = "csv"  # Default to CSV for backward compatibility

        logger.info(
            f"Reading blob with format: {data_format}",
            extra={
                "event": "blob_read_format_detected",
                "source": "blob",
                "format": data_format,
            },
        )

        try:
            service_client = self._get_service_client()
            container_client = service_client.get_container_client(self.blob_container)
            blob_client = container_client.get_blob_client(self.blob_path)

            logger.info(
                "Blob read started",
                extra={
                    "event": "blob_read_started",
                    "source": "blob",
                    "status": "started",
                    "format": data_format,
                },
            )

            # Download blob content into bytes buffer
            download_stream = blob_client.download_blob()
            blob_bytes = download_stream.readall()

            # Parse according to format
            if data_format == "csv":
                df = read_csv_with_fallback(io.BytesIO(blob_bytes))
            elif data_format == "json":
                df = pd.read_json(io.BytesIO(blob_bytes))
            elif data_format == "parquet":
                df = pd.read_parquet(io.BytesIO(blob_bytes))
            elif data_format in ("xlsx", "excel", "xls"):
                # Use openpyxl engine for xlsx files, xlrd for older xls
                df = pd.read_excel(io.BytesIO(blob_bytes))
            else:
                raise ValueError(f"Unsupported blob format: {data_format}")

            df = normalize_loaded_dataframe(df)

            logger.info(
                "Blob read completed",
                extra={
                    "event": "blob_read_completed",
                    "source": "blob",
                    "status": "success",
                    "format": data_format,
                    "rows": len(df),
                },
            )
            return {
                "status": "success",
                "rows": df,
                "source": "blob",
            }

        except CsvDecodingError:
            # CSV decoding errors should propagate as-is
            raise

        except ClientAuthenticationError as e:
            error_msg = (
                f"Authentication/authorization failed for "
                f"account={self.blob_account}, container={self.blob_container}"
            )
            logger.error(
                error_msg,
                extra={
                    "event": "blob_authentication_failed",
                    "source": "blob",
                    "status": "failed",
                    "error_type": "blob_authentication_error",
                    "error_message": str(e),
                },
            )
            raise BlobAuthenticationError(error_msg, str(e)) from e

        except ResourceNotFoundError as e:
            # Distinguish between container not found and blob not found
            if "ContainerNotFound" in str(e):
                error_msg = f"Container '{self.blob_container}' not found"
            else:
                error_msg = f"Blob '{self.blob_path}' not found in container '{self.blob_container}'"
            logger.error(
                error_msg,
                extra={
                    "event": "blob_not_found",
                    "source": "blob",
                    "status": "failed",
                    "error_type": "blob_not_found_error",
                    "error_message": str(e),
                },
            )
            raise BlobNotFoundError(error_msg, str(e)) from e

        except (ServiceRequestError, HttpResponseError) as e:
            # Network-level errors or transient HTTP errors
            error_msg = (
                f"Network error accessing Blob Storage "
                f"(account={self.blob_account})"
            )
            logger.error(
                error_msg,
                extra={
                    "event": "blob_network_error",
                    "source": "blob",
                    "status": "failed",
                    "error_type": "blob_network_error",
                    "error_message": str(e),
                },
            )
            raise BlobNetworkError(error_msg, str(e)) from e

        except Exception as e:
            # Catch other potential errors and categorize as network or value error
            if isinstance(e, ValueError):
                raise
            error_msg = f"Unexpected error reading blob: {type(e).__name__}"
            logger.error(
                error_msg,
                extra={
                    "event": "blob_network_error",
                    "source": "blob",
                    "status": "failed",
                    "error_type": "blob_network_error",
                    "error_message": str(e),
                },
            )
            raise BlobNetworkError(error_msg, str(e)) from e


def read_blob_csv(
    blob_account: Optional[str],
    blob_container: str,
    blob_path: str,
    connection_string: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience function to read CSV from Blob Storage.

    This is the main entry point for the ingestion layer to read from Blob.

    Args:
        blob_account: Storage account name
        blob_container: Container name
        blob_path: Path within container
        connection_string: Optional connection string for transitional auth

    Returns:
        dict with status, rows (DataFrame), and source metadata

    Raises:
        BlobAuthenticationError: If auth/permission fails
        BlobNotFoundError: If blob/container not found
        BlobNetworkError: If connectivity issue occurs
    """
    client = BlobClient(
        blob_account=blob_account,
        blob_container=blob_container,
        blob_path=blob_path,
        connection_string=connection_string,
    )
    return client.read_blob_csv()


def read_blob_data(
    blob_account: Optional[str],
    blob_container: str,
    blob_path: str,
    connection_string: Optional[str] = None,
    data_format: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Format-aware function to read data from Blob Storage.

    Dispatches to format-specific readers based on data_format parameter.
    This is the new entry point for format-aware blob ingestion.

    Args:
        blob_account: Storage account name
        blob_container: Container name
        blob_path: Path within container
        connection_string: Optional connection string for transitional auth
        data_format: Format specification (csv/json/parquet/xlsx)
                     If None, attempts to detect from blob_path extension

    Returns:
        dict with status, rows (DataFrame), and source metadata

    Raises:
        BlobAuthenticationError: If auth/permission fails
        BlobNotFoundError: If blob/container not found
        BlobNetworkError: If connectivity issue occurs
        ValueError: If format is unsupported
    """
    client = BlobClient(
        blob_account=blob_account,
        blob_container=blob_container,
        blob_path=blob_path,
        connection_string=connection_string,
    )
    return client.read_blob_data(data_format=data_format)
