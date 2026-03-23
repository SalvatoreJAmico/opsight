"""
Opsight Ingestion Layer
PS-094: Centralized ingestion with dev/prod source separation

Dev mode:
  - Local INPUT_SOURCE_PATH preferred
  - Blob as secondary option if configured
  - Explicit fallback allowed via config

Prod mode:
  - Blob Storage mandatory (managed identity or connection string)
  - No local file fallback
  - Auth/network errors fail clearly
"""

import os
import logging
from pathlib import Path

import pandas as pd

from modules.config.runtime_config import load_runtime_config
from modules.ingestion.blob_client import (
    read_blob_csv,
    BlobAuthenticationError,
    BlobNotFoundError,
    BlobNetworkError,
)

logger = logging.getLogger(__name__)

# Cache config to avoid reloading
_cached_config = None


def _get_runtime_config():
    """Get cached runtime config."""
    global _cached_config
    if _cached_config is None:
        _cached_config = load_runtime_config()
    return _cached_config


# PS-003: Implement ingestion record validation
# Validates that a record contains the required fields defined in the ingestion data contract.


def validate_record(record):
    required_fields = ["timestamp", "source", "event_type"]
    for field in required_fields:
        if field not in record:
            return False
    return True


def detect_format(source_path: str) -> str:
    """
    Detect the format of the incoming data source.
    """
    if source_path.startswith("sql://"):
        return "sql"

    path = Path(source_path)

    with open(source_path, "rb") as file_handle:
        header = file_handle.read(4)

    if b"{" in header or b"[" in header:
        return "json"
    if b"PAR1" in header:
        return "parquet"
    if b"PK" in header and path.suffix.lower() in {".xlsx", ".xlsm", ".xltx", ".xltm"}:
        return "excel"

    with open(source_path, "r", encoding="utf-8", errors="ignore") as file_handle:
        sample_text = file_handle.readline()

    if "," in sample_text:
        return "csv"
    if "\t" in sample_text:
        return "tsv"
    return "text"


def load_source(source_path: str, source_format: str):
    """
    Load source data into a dataframe-like structure.
    """
    if source_format == "sql":
        return pd.DataFrame()
    if source_format == "csv":
        return pd.read_csv(source_path)
    if source_format == "tsv":
        return pd.read_csv(source_path, sep="\t")
    if source_format == "json":
        return pd.read_json(source_path)
    if source_format == "parquet":
        return pd.read_parquet(source_path)
    if source_format == "excel":
        return pd.read_excel(source_path)

    raise ValueError(f"Unsupported source format: {source_format}")


def _load_local_file(source_path: str) -> pd.DataFrame:
    """
    Load data from a local file system path.

    Args:
        source_path: Local file path

    Returns:
        pandas.DataFrame with file content

    Raises:
        FileNotFoundError: If file not found
        ValueError: If format unsupported
    """
    logger.debug(f"Loading data from local file: {source_path}")
    source_format = detect_format(source_path)
    return load_source(source_path, source_format)


def _load_from_blob(
    blob_account: str,
    blob_container: str,
    blob_path: str,
    connection_string: str = None,
) -> pd.DataFrame:
    """
    Load data from Azure Blob Storage.

    Args:
        blob_account: Storage account name
        blob_container: Container name
        blob_path: Path within container
        connection_string: Optional connection string for transitional auth

    Returns:
        pandas.DataFrame with blob content

    Raises:
        BlobAuthenticationError: If auth/permission fails
        BlobNotFoundError: If blob/container not found
        BlobNetworkError: If connectivity issue occurs
    """
    logger.debug(
        f"Loading data from Blob Storage: "
        f"account={blob_account}, container={blob_container}, path={blob_path}"
    )
    blob_result = read_blob_csv(
        blob_account=blob_account,
        blob_container=blob_container,
        blob_path=blob_path,
        connection_string=connection_string,
    )
    logger.debug(
        "Blob read completed with status=%s source=%s",
        blob_result.get("status"),
        blob_result.get("source"),
    )
    return blob_result["rows"]


def ingest_data(source_path: str = None, source_mode: str = None) -> pd.DataFrame:
    """
    Ingest data based on runtime configuration and source mode.

    PS-094 routing rules with source_mode enforcement:
    
    EXPLICIT SOURCE_MODE (from frontend target selection):
      - source_mode="local": Use local file only, no blob fallback
      - source_mode="cloud": Use blob only, no local file
      - No cross-mode fallback allowed
    
    FALLBACK (source_mode=None, for backward compatibility):
      PRODUCTION MODE (APP_ENV=prod):
        - Blob Storage is mandatory ingestion source
        - No local file fallback, ever
        - Auth/network errors fail immediately
      
      DEVELOPMENT MODE (APP_ENV=dev):
        - Local INPUT_SOURCE_PATH preferred (if configured)
        - Blob as fallback if explicitly enabled
        - Easy local testing remains intact

    Args:
        source_path: Optional override path (for testing/explicit calls).
                    If provided, takes precedence over config.
        source_mode: Optional mode selection ("local" or "cloud") from frontend target.
                    If set, enforces strict behavior without fallback.

    Returns:
        pandas.DataFrame with ingested data

    Raises:
        ValueError: If no valid source configured
        FileNotFoundError: If local file not found (dev mode or local mode)
        BlobAuthenticationError: If Blob auth fails (prod or blob-sourced)
        BlobNotFoundError: If Blob resource not found (prod or blob-sourced)
        BlobNetworkError: If Blob network error occurs (prod or blob-sourced)
    """
    config = _get_runtime_config()

    # ===== STRICT SOURCE_MODE: No fallback =====
    if source_mode == "local":
        logger.info("Source mode: local (strict, no blob fallback)")

        # Try explicit source_path first if provided
        if source_path:
            logger.info(f"Using explicit source path: {source_path}")
            return _load_local_file(source_path)

        # Use configured INPUT_SOURCE_PATH
        if config.input_source_path and config.input_source_path.strip():
            logger.debug(f"Attempting local file from config: {config.input_source_path}")
            return _load_local_file(config.input_source_path)

        # No local source available
        raise ValueError(
            "Local mode requested but no local source configured. "
            "Set INPUT_SOURCE_PATH environment variable."
        )

    if source_mode == "cloud":
        logger.info("Source mode: cloud (strict, blob only)")

        # Cloud mode requires blob configuration
        if not config.blob_account or not config.blob_container or not config.blob_path:
            raise ValueError(
                "Cloud mode requested but Blob Storage not fully configured. "
                "Set BLOB_ACCOUNT, BLOB_CONTAINER, and BLOB_PATH."
            )

        # Use configured blob path
        try:
            return _load_from_blob(
                blob_account=config.blob_account,
                blob_container=config.blob_container,
                blob_path=config.blob_path,
                connection_string=config.azure_storage_connection_string,
            )
        except (BlobAuthenticationError, BlobNotFoundError, BlobNetworkError):
            # Blob errors fail immediately in cloud mode
            raise

    if source_path:
        logger.info(f"Using explicit source path: {source_path}")

        if source_path.startswith(("http://", "https://")):
            source_lower = source_path.lower()
            if source_lower.endswith(".csv"):
                return pd.read_csv(source_path)
            if source_lower.endswith(".json"):
                return pd.read_json(source_path)
            if source_lower.endswith(".parquet"):
                return pd.read_parquet(source_path)
            if source_lower.endswith((".xlsx", ".xlsm", ".xltx", ".xltm", ".xls")):
                return pd.read_excel(source_path)

        local_path = Path(source_path)

        # Treat container/blob style paths as Azure Blob paths when they are not
        # explicit local path forms (absolute path, ./relative, ../relative).
        if (
            "/" in source_path
            and (config.blob_account or config.azure_storage_connection_string)
            and not local_path.is_absolute()
            and not source_path.startswith(("./", "../", "/"))
            and not local_path.exists()
        ):
            blob_container, blob_path = source_path.split("/", 1)
            if blob_container and blob_path:
                logger.info(
                    "Using explicit Blob source path: container=%s path=%s",
                    blob_container,
                    blob_path,
                )
                return _load_from_blob(
                    blob_account=config.blob_account,
                    blob_container=blob_container,
                    blob_path=blob_path,
                    connection_string=config.azure_storage_connection_string,
                )

        return _load_local_file(source_path)

    # ===== PRODUCTION MODE: Blob mandatory =====
    if config.app_env == "prod":
        logger.info("Production mode: using Blob Storage as ingestion source")
        try:
            return _load_from_blob(
                blob_account=config.blob_account,
                blob_container=config.blob_container,
                blob_path=config.blob_path,
                connection_string=config.azure_storage_connection_string,
            )
        except (BlobAuthenticationError, BlobNotFoundError, BlobNetworkError):
            # Auth/network errors fail immediately in production
            raise

    # ===== DEVELOPMENT MODE: Local preferred, Blob fallback =====
    if config.app_env == "dev":
        logger.info("Development mode: trying local file first, Blob fallback if enabled")

        # Try local file first (if configured)
        if config.input_source_path and config.input_source_path.strip():
            try:
                logger.debug(f"Attempting local file: {config.input_source_path}")
                return _load_local_file(config.input_source_path)
            except FileNotFoundError:
                logger.warning(
                    f"Local file not found: {config.input_source_path}. "
                    f"Checking for Blob fallback..."
                )
            except Exception as e:
                logger.warning(f"Error loading local file: {e}. Checking for Blob fallback...")

        # Blob fallback in dev (if configured)
        if (
            config.allow_local_fallback
            and config.blob_account
            and config.blob_container
            and config.blob_path
        ):
            logger.debug("Attempting Blob fallback (allowed in dev)")
            try:
                return _load_from_blob(
                    blob_account=config.blob_account,
                    blob_container=config.blob_container,
                    blob_path=config.blob_path,
                    connection_string=config.azure_storage_connection_string,
                )
            except (BlobAuthenticationError, BlobNotFoundError, BlobNetworkError) as e:
                logger.warning(f"Blob fallback failed: {e}")
                raise

        # No valid source found
        raise ValueError(
            "No valid data source configured. "
            "In dev mode, set INPUT_SOURCE_PATH or enable Blob (BLOB_ACCOUNT, BLOB_CONTAINER, BLOB_PATH)."
        )

    raise RuntimeError(f"Unknown APP_ENV: {config.app_env}")
