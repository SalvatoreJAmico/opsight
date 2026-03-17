"""
Opsight Pipeline Runner
Phase 4 – Pipeline Orchestration

Runs the full Opsight pipeline end-to-end.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from modules.ingestion.ingestion import ingest_data
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
    runtime_config = load_runtime_config()
    setup_logging(service_name="opsight.pipeline")

    start_time = datetime.now(timezone.utc)
    logger.info("Pipeline started", extra={"event": "pipeline_started"})
    status = "SUCCESS"
    failed_stage = None

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
            if input_data is None:
                if not runtime_config.input_source_path:
                    raise RuntimeError("Missing required environment variable: INPUT_SOURCE_PATH")
                source_path = runtime_config.input_source_path
            else:
                source_path = input_data

            raw_data = ingest_data(source_path)
            logger.info(
                "Stage completed",
                extra={
                    "event": "stage_completed",
                    "stage": "ingestion",
                    "records_ingested": len(raw_data),
                },
            )
        except Exception as e:
            failed_stage = "ingestion"
            logger.exception(
                "Stage failed",
                extra={"event": "stage_failed", "stage": failed_stage},
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
            logger.exception(
                "Stage failed",
                extra={"event": "stage_failed", "stage": failed_stage},
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
            logger.exception(
                "Stage failed",
                extra={"event": "stage_failed", "stage": failed_stage},
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
                if runtime_config.enable_pipeline:
                    df = detect_anomalies(valid_records)
                    df = score_records(df)
                    metrics = evaluate(df)
                    print("Intelligence Metrics:", metrics)
                logger.info(
                    "Stage completed",
                    extra={"event": "stage_completed", "stage": "intelligence"},
                )
            except Exception as intelligence_error:
                logger.exception(
                    "Stage failed (non-blocking)",
                    extra={"event": "stage_failed", "stage": "intelligence"},
                )
        except Exception as e:
            failed_stage = "persistence"
            logger.exception(
                "Stage failed",
                extra={"event": "stage_failed", "stage": failed_stage},
            )
            raise RuntimeError(f"Persistence failed: {e}") from e
       
    except Exception as e:
        status = "FAILED"
        logger.exception(
            "Pipeline failed",
            extra={
                "event": "pipeline_failed",
                "failed_stage": failed_stage,
            },
        )
    finally:
        end_time = datetime.now(timezone.utc)
        runtime_seconds = (end_time - start_time).total_seconds()
        logger.info(
            "Pipeline finished",
            extra={
                "event": "pipeline_finished",
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

    print(summary)
    with open(REPORTS_DIR / "pipeline_run_summary.json", "w") as f:
        json.dump(summary, f, indent=4)

    if status == "FAILED":
        with open(REPORTS_DIR / "pipeline_failure_summary.json", "w") as f:
            json.dump(summary, f, indent=4)

    return summary

if __name__ == "__main__":
    run_pipeline()