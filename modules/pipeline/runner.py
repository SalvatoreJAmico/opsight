"""
Opsight Pipeline Runner

Orchestrates the full pipeline:
    ingestion → adapter → validation → persistence
"""

import logging
from datetime import datetime, timezone

from modules.ingestion.ingestion import detect_format, load_source
from modules.adapter.adapter import normalize_record, to_canonical_schema
from modules.validation.batch_validator import validate_batch
from modules.validation.duplicate_check import detect_duplicates
from modules.validation.report import generate_validation_report
from modules.persistence.persistence_manager import PersistenceManager
from modules.config.storage_config import StorageConfig

logger = logging.getLogger(__name__)


def _to_native(value):
    """Convert a pandas/numpy scalar to a native Python type."""
    if hasattr(value, "item"):
        return value.item()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _convert_record(record):
    """Return a canonical record with all values as JSON-serializable Python types."""
    return {
        "entity_id": _to_native(record.get("entity_id")),
        "timestamp": _to_native(record.get("timestamp")),
        "features": {k: _to_native(v) for k, v in record.get("features", {}).items()},
        "metadata": {k: _to_native(v) for k, v in record.get("metadata", {}).items()},
    }


def run_pipeline(source_path: str, config: StorageConfig = None) -> dict:
    """
    Execute the full Opsight pipeline.

    Stages:
        1. Ingestion  - detect format and load source data
        2. Adapter    - normalize and convert to canonical schema
        3. Validation - validate batch and detect duplicates
        4. Persistence - persist records to the configured storage backend

    Args:
        source_path: Path to the source data file.
        config: Storage configuration. Defaults to JSON backend.

    Returns:
        dict: Pipeline execution summary containing stage results and record counts.
    """
    if config is None:
        config = StorageConfig()

    started_at = datetime.now(timezone.utc).isoformat()
    logger.info("Pipeline started at %s", started_at)

    summary = {
        "started_at": started_at,
        "source_path": source_path,
        "stages": {},
        "records_ingested": 0,
        "records_adapted": 0,
        "records_valid": 0,
        "records_invalid": 0,
        "duplicates_found": 0,
        "records_persisted": 0,
        "status": "failed",
        "errors": [],
    }

    try:
        # Stage 1: Ingestion
        logger.info("Stage 1/4: Ingestion - loading source: %s", source_path)
        source_format = detect_format(source_path)
        dataframe = load_source(source_path, source_format)
        summary["records_ingested"] = len(dataframe)
        summary["stages"]["ingestion"] = "complete"
        logger.info("Ingestion complete. Records loaded: %d", summary["records_ingested"])

        # Stage 2: Adapter
        logger.info("Stage 2/4: Adapter - transforming to canonical schema")
        normalized = normalize_record(dataframe)
        canonical_records = to_canonical_schema(normalized)
        canonical_records = [_convert_record(r) for r in canonical_records]
        summary["records_adapted"] = len(canonical_records)
        summary["stages"]["adapter"] = "complete"
        logger.info("Adapter complete. Records adapted: %d", summary["records_adapted"])

        # Stage 3: Validation
        logger.info("Stage 3/4: Validation - validating canonical records")
        validation_results = validate_batch(canonical_records)
        duplicate_results = detect_duplicates(canonical_records)
        validation_report = generate_validation_report(validation_results)
        summary["records_valid"] = validation_report["valid_records"]
        summary["records_invalid"] = validation_report["invalid_records"]
        summary["duplicates_found"] = len(duplicate_results["duplicate_records"])
        summary["stages"]["validation"] = "complete"
        logger.info(
            "Validation complete. Valid: %d, Invalid: %d, Duplicates: %d",
            summary["records_valid"],
            summary["records_invalid"],
            summary["duplicates_found"],
        )

        if summary["records_invalid"] > 0:
            logger.warning(
                "Validation failures: %d records invalid", summary["records_invalid"]
            )
            for entry in validation_report["errors"]:
                logger.warning("  Record %d: %s", entry["record_index"], entry["errors"])

        # Stage 4: Persistence
        logger.info("Stage 4/4: Persistence - storing records")
        manager = PersistenceManager(config)
        manager.persist_records(canonical_records)
        summary["records_persisted"] = len(canonical_records)
        summary["stages"]["persistence"] = "complete"
        logger.info("Persistence complete. Records stored: %d", summary["records_persisted"])

        summary["status"] = "success"

    except Exception as exc:
        summary["errors"].append(str(exc))
        summary["status"] = "failed"
        logger.error("Pipeline failed: %s", exc)

    finally:
        ended_at = datetime.now(timezone.utc).isoformat()
        summary["ended_at"] = ended_at
        logger.info(
            "Pipeline ended at %s with status: %s", ended_at, summary["status"]
        )

    return summary
