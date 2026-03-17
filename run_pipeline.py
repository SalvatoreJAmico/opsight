"""
Opsight Pipeline Runner
Phase 4 – Pipeline Orchestration

Runs the full Opsight pipeline end-to-end.
PS-094: Config-driven ingestion source (Blob/Local) with clear error handling.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from modules.ingestion.ingestion import ingest_data
from modules.ingestion.blob_client import (
    BlobAuthenticationError,
    BlobNotFoundError,
    BlobNetworkError,
)
from modules.adapter.adapter import adapt_records
from modules.validation.validator import validate_canonical_record
from modules.intelligence import detect_anomalies, score_records, evaluate

from modules.persistence.storage_factory import StorageFactory
from modules.config.storage_config import StorageConfig
from modules.config.logging_config import setup_logging
from modules.config.runtime_config import load_runtime_config

# TODO:
# Replace broad Exception catches with stage-specific exception types as modules mature.
# TODO:
# Move stage logging into a reusable pipeline logger utility later.
PROJECT_ROOT = Path(__file__).resolve().parent

REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("opsight.pipeline")

def run_pipeline(input_data=None):
    setup_logging(service_name="opsight.pipeline")
    try:
        runtime_config = load_runtime_config()
    except Exception as exc:
        logger.error(
            "Runtime config load failed before pipeline execution",
            extra={
                "event": "runtime_config_error",
                "error_type": "runtime_config_error",
                "error_message": str(exc),
            },
        )
        raise

    logger.info(
        "Runtime configuration loaded",
        extra={
            "event": "runtime_config_loaded",
            "app_env": runtime_config.app_env,
            "app_version": runtime_config.app_version,
            "persistence_mode": runtime_config.persistence_mode,
            "port": runtime_config.port,
        },
    )

    summary_path = Path(runtime_config.pipeline_summary_path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    failure_summary_path = summary_path.with_name("pipeline_failure_summary.json")

    start_time = datetime.now(timezone.utc)
    source = "explicit" if input_data else ("blob" if runtime_config.app_env == "prod" else "local_or_blob_fallback")
    logger.info(
        "Pipeline execution started",
        extra={
            "event": "pipeline_execution_started",
            "status": "started",
            "source": source,
        },
    )
    status = "SUCCESS"
    failed_stage = None
    pipeline_error_type = None
    pipeline_error_message = None

    raw_data = None
    canonical_records = []
    valid_records = []
    invalid_records = []

    try:
        # -------------------------
        # Stage 1: Ingestion
        # -------------------------
        try:
            logger.info(
                "Stage started",
                extra={"event": "stage_started", "stage": "ingestion"},
            )
            
            # PS-094: Config-driven ingestion routing
            # Calls ingest_data() with optional source_path override for testing
            # Config determines: Blob in prod, Local/Blob fallback in dev
            raw_data = ingest_data(source_path=input_data)
            
            logger.info(
                "Stage completed",
                extra={
                    "event": "stage_completed",
                    "stage": "ingestion",
                    "source": source,
                    "records_ingested": len(raw_data),
                },
            )
        except BlobAuthenticationError as e:
            failed_stage = "ingestion"
            pipeline_error_type = "blob_authentication_error"
            pipeline_error_message = str(e)
            logger.error(
                "Blob authentication failed",
                extra={
                    "event": "blob_authentication_failed",
                    "stage": failed_stage,
                    "source": "blob",
                    "status": "failed",
                    "error_type": pipeline_error_type,
                    "error_message": pipeline_error_message,
                },
            )
            raise RuntimeError(f"Ingestion failed - Blob authentication error: {e}") from e
        except BlobNotFoundError as e:
            failed_stage = "ingestion"
            pipeline_error_type = "blob_not_found_error"
            pipeline_error_message = str(e)
            logger.error(
                "Blob resource not found",
                extra={
                    "event": "blob_not_found",
                    "stage": failed_stage,
                    "source": "blob",
                    "status": "failed",
                    "error_type": pipeline_error_type,
                    "error_message": pipeline_error_message,
                },
            )
            raise RuntimeError(f"Ingestion failed - Blob not found: {e}") from e
        except BlobNetworkError as e:
            failed_stage = "ingestion"
            pipeline_error_type = "blob_network_error"
            pipeline_error_message = str(e)
            logger.error(
                "Blob network error",
                extra={
                    "event": "blob_network_error",
                    "stage": failed_stage,
                    "source": "blob",
                    "status": "failed",
                    "error_type": pipeline_error_type,
                    "error_message": pipeline_error_message,
                },
            )
            raise RuntimeError(f"Ingestion failed - Blob network error: {e}") from e
        except Exception as e:
            failed_stage = "ingestion"
            pipeline_error_type = "pipeline_execution_error"
            pipeline_error_message = str(e)
            logger.exception(
                "Stage failed",
                extra={
                    "event": "stage_failed",
                    "stage": failed_stage,
                    "status": "failed",
                    "error_type": pipeline_error_type,
                    "error_message": pipeline_error_message,
                },
            )
            raise RuntimeError(f"Ingestion failed: {e}") from e
    
        # -------------------------
        # Stage 2: Adapter
        # -------------------------
        try:
            logger.info(
                "Stage started",
                extra={"event": "stage_started", "stage": "adapter"},
            )
            canonical_records = adapt_records(raw_data)
            logger.info(
                "Stage completed",
                extra={
                    "event": "stage_completed",
                    "stage": "adapter",
                    "records_ingested": len(raw_data),
                },
            )
        except Exception as e:
            failed_stage = "adapter"
            pipeline_error_type = "pipeline_execution_error"
            pipeline_error_message = str(e)
            logger.exception(
                "Stage failed",
                extra={
                    "event": "stage_failed",
                    "stage": failed_stage,
                    "status": "failed",
                    "error_type": pipeline_error_type,
                    "error_message": pipeline_error_message,
                },
            )
            raise RuntimeError(f"Adapter failed: {e}") from e
        

        # -------------------------
        # Stage 3: Validation
        # -------------------------
        try:
            logger.info(
                "Stage started",
                extra={"event": "stage_started", "stage": "validation"},
            )

            for record in canonical_records:
                result = validate_canonical_record(record)

                if result["status"] == "valid":
                    valid_records.append(record)
                else:
                    invalid_records.append(record)

            logger.info(
                "Stage completed",
                extra={
                    "event": "stage_completed",
                    "stage": "validation",
                    "records_valid": len(valid_records),
                    "records_invalid": len(invalid_records),
                },
            )
        except Exception as e:
            failed_stage = "validation"
            pipeline_error_type = "pipeline_execution_error"
            pipeline_error_message = str(e)
            logger.exception(
                "Stage failed",
                extra={
                    "event": "stage_failed",
                    "stage": failed_stage,
                    "status": "failed",
                    "error_type": pipeline_error_type,
                    "error_message": pipeline_error_message,
                },
            )
            raise RuntimeError(f"Validation failed: {e}") from e

        # -------------------------
        # Stage 4: Persistence
        # -------------------------
        try:
            logger.info(
                "Stage started",
                extra={"event": "stage_started", "stage": "persistence"},
            )
            storage_config = StorageConfig()
            storage = StorageFactory.create_storage(storage_config)
            storage.save_records(valid_records)
            logger.info(
                "Stage completed",
                extra={
                    "event": "stage_completed",
                    "stage": "persistence",
                    "records_persisted": len(valid_records),
                },
            )

            # Stage 5: Intelligence (best-effort, non-blocking)
            try:
                logger.info(
                    "Stage started",
                    extra={"event": "stage_started", "stage": "intelligence"},
                )
                df = detect_anomalies(valid_records)
                df = score_records(df)
                metrics = evaluate(df)
                logger.info(
                    "Stage completed",
                    extra={
                        "event": "stage_completed",
                        "stage": "intelligence",
                        "status": "success",
                    },
                )
            except Exception as intelligence_error:
                logger.warning(
                    "Stage failed (non-blocking)",
                    extra={
                        "event": "stage_failed",
                        "stage": "intelligence",
                        "status": "failed",
                        "error_type": "pipeline_execution_error",
                        "error_message": str(intelligence_error),
                    },
                )
        except Exception as e:
            failed_stage = "persistence"
            pipeline_error_type = "pipeline_execution_error"
            pipeline_error_message = str(e)
            logger.exception(
                "Stage failed",
                extra={
                    "event": "stage_failed",
                    "stage": failed_stage,
                    "status": "failed",
                    "error_type": pipeline_error_type,
                    "error_message": pipeline_error_message,
                },
            )
            raise RuntimeError(f"Persistence failed: {e}") from e
       
    except Exception as e:
        status = "FAILED"
        if pipeline_error_type is None:
            pipeline_error_type = "pipeline_execution_error"
        if pipeline_error_message is None:
            pipeline_error_message = str(e)
        logger.exception(
            "Pipeline execution failed",
            extra={
                "event": "pipeline_execution_failed",
                "status": "failed",
                "error_type": pipeline_error_type,
                "error_message": pipeline_error_message,
                "failed_stage": failed_stage,
            },
        )
    finally:
        end_time = datetime.now(timezone.utc)
        runtime_seconds = (end_time - start_time).total_seconds()
        if status == "SUCCESS":
            logger.info(
                "Pipeline execution completed",
                extra={
                    "event": "pipeline_execution_completed",
                    "status": "success",
                    "runtime_seconds": runtime_seconds,
                    "failed_stage": failed_stage,
                },
            )

    summary = {
        "status": status,
        "failed_stage": failed_stage,
        "records_ingested": len(raw_data) if raw_data is not None else 0,
        "records_valid": len(valid_records),
        "records_invalid": len(invalid_records),
        "records_persisted": len(valid_records) if status == "SUCCESS" else 0,
        "runtime_seconds": runtime_seconds,

    }

    logger.info(
        "Pipeline metrics",
        extra={
            "event": "pipeline_metrics",
            "records_ingested": summary["records_ingested"],
            "records_valid": summary["records_valid"],
            "records_invalid": summary["records_invalid"],
            "records_persisted": summary["records_persisted"],
            "runtime_seconds": summary["runtime_seconds"],
            "failed_stage": summary["failed_stage"],
        },
    )

    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=4)

    if status == "FAILED":
        with open(failure_summary_path, "w") as f:
            json.dump(summary, f, indent=4)

    return summary

if __name__ == "__main__":
    run_pipeline()