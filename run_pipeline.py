"""
Opsight Pipeline Runner
Phase 4 – Pipeline Orchestration

Runs the full Opsight pipeline end-to-end.
"""

from modules.ingestion.ingestion import ingest_data
from modules.adapter.adapter import adapt_records
from modules.validation.validator import validate_canonical_record

from modules.persistence.storage_factory import StorageFactory
from configs.storage_config import StorageConfig

import logging
from datetime import datetime, timezone
from pathlib import Path

# TODO:
# Move stage logging into a reusable pipeline logger utility later.
PROJECT_ROOT = Path(__file__).resolve().parent
LOG_DIR = PROJECT_ROOT / "logs"

# TODO:
# Move DATA_SOURCE and logging settings into a pipeline config file later.
DATA_SOURCE = str(PROJECT_ROOT / "data" / "opsight_sample_sales.csv")

LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOG_DIR / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def run_pipeline():

    start_time = datetime.now(timezone.utc)
    logging.info("Pipeline started")

    # -------------------------
    # Stage 1: Ingestion
    # -------------------------
    logging.info("Stage: ingestion started")

    raw_data = ingest_data(DATA_SOURCE)

    logging.info("Stage: ingestion completed")

    # -------------------------
    # Stage 2: Adapter
    # -------------------------
    logging.info("Stage: adapter started")

    canonical_records = adapt_records(raw_data)

    logging.info(f"Stage: adapter completed | records={len(canonical_records)}")

    # -------------------------
    # Stage 3: Validation
    # -------------------------
    logging.info("Stage: validation started")

    valid_records = []
    invalid_records = []

    for record in canonical_records:
        result = validate_canonical_record(record)

        if result["status"] == "valid":
            valid_records.append(record)
        else:
            invalid_records.append(record)

    logging.info(
        f"Stage: validation completed | valid={len(valid_records)} invalid={len(invalid_records)}"
    )

    # -------------------------
    # Stage 4: Persistence
    # -------------------------
    logging.info("Stage: persistence started")

    storage_config = StorageConfig(backend="json")
    storage = StorageFactory.create_storage(storage_config)

    storage.save_records(valid_records)

    logging.info("Stage: persistence completed")

    end_time = datetime.now(timezone.utc)

    logging.info(f"Pipeline finished | runtime={end_time - start_time}")

    # console summary
    print("Pipeline completed")
    print(f"Valid records: {len(valid_records)}")
    print(f"Invalid records: {len(invalid_records)}")
    print(f"Log file: {LOG_DIR}")

if __name__ == "__main__":
    run_pipeline()