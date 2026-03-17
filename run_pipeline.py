"""
Opsight Pipeline Runner
Phase 4 – Pipeline Orchestration

Runs the full Opsight pipeline end-to-end.
"""
import json
from modules.ingestion.ingestion import ingest_data
from modules.adapter.adapter import adapt_records
from modules.validation.validator import validate_canonical_record
from modules.intelligence import detect_anomalies, score_records, evaluate

from modules.persistence.storage_factory import StorageFactory
from modules.config.storage_config import StorageConfig

import logging
from datetime import datetime, timezone
from pathlib import Path
# TODO:
# Replace broad Exception catches with stage-specific exception types as modules mature.
# TODO:
# Move stage logging into a reusable pipeline logger utility later.
PROJECT_ROOT = Path(__file__).resolve().parent
LOG_DIR = PROJECT_ROOT / "logs"

REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# TODO:
# Move DATA_SOURCE and logging settings into a pipeline config file later.
DATA_SOURCE = str(PROJECT_ROOT / "data" / "opsight_sample_sales.csv")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOG_DIR / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def run_pipeline(input_data=None):

    start_time = datetime.now(timezone.utc)
    logging.info("Pipeline started")
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
            logging.info("Stage: ingestion started")
            raw_data = ingest_data(DATA_SOURCE) if input_data is None else ingest_data(input_data)
            logging.info("Stage: ingestion completed")
        except Exception as e:
            failed_stage = "ingestion"
            raise RuntimeError(f"Ingestion failed: {e}") from e
    
        # -------------------------
        # Stage 2: Adapter
        # -------------------------
        try:
            logging.info("Stage: adapter started")
            canonical_records = adapt_records(raw_data)
            logging.info(f"Stage: adapter completed | records={len(canonical_records)}")
        except Exception as e:
            failed_stage = "adapter"
            raise RuntimeError(f"Adapter failed: {e}") from e
        

        # -------------------------
        # Stage 3: Validation
        # -------------------------
        try:
            logging.info("Stage: validation started")

            for record in canonical_records:
                result = validate_canonical_record(record)

                if result["status"] == "valid":
                    valid_records.append(record)
                else:
                    invalid_records.append(record)

            logging.info(
                f"Stage: validation completed | valid={len(valid_records)} invalid={len(invalid_records)}"
            )
        except Exception as e:
            failed_stage = "validation"
            raise RuntimeError(f"Validation failed: {e}") from e

        # -------------------------
        # Stage 4: Persistence
        # -------------------------
        try:
            logging.info("Stage: persistence started")
            storage_config = StorageConfig(backend="json")
            storage = StorageFactory.create_storage(storage_config)
            storage.save_records(valid_records)
            logging.info("Stage: persistence completed")

            # Stage 5: Intelligence (best-effort, non-blocking)
            try:
                df = detect_anomalies(valid_records)
                df = score_records(df)
                metrics = evaluate(df)
                print("Intelligence Metrics:", metrics)
                logging.info("Stage: intelligence completed")
            except Exception as intelligence_error:
                logging.warning(f"Stage: intelligence failed (non-blocking): {intelligence_error}")
        except Exception as e:
            failed_stage = "persistence"
            raise RuntimeError(f"Persistence failed: {e}") from e
       
    except Exception as e:
        status = "FAILED"
        logging.exception(f"Pipeline failed with error: | status={status} | {str(e)}")
    finally:
        end_time = datetime.now(timezone.utc)
        logging.info(f"Pipeline finished | status={status} | runtime={end_time - start_time}")

    summary = {
        "status": status,
        "failed_stage": failed_stage,
        "records_ingested": len(raw_data) if raw_data is not None else 0,
        "records_valid": len(valid_records),
        "records_invalid": len(invalid_records),
        "records_persisted": len(valid_records) if status == "SUCCESS" else 0,
        "runtime_seconds": (end_time - start_time).total_seconds(),

    }

    print(summary)
    with open(REPORTS_DIR / "pipeline_run_summary.json", "w") as f:
        json.dump(summary, f, indent=4)

    if status == "FAILED":
        with open(REPORTS_DIR / "pipeline_failure_summary.json", "w") as f:
            json.dump(summary, f, indent=4)

    return summary

if __name__ == "__main__":
    run_pipeline()