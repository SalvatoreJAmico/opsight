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


def run_pipeline():

    print("Starting Opsight pipeline")

    # Step 1 — Ingestion
    source_path = "https://stopsightdev.blob.core.windows.net/opsight-raw/csv/opsight_sample_sales.csv"
    try:
        raw_data = ingest_data(source_path)
    except Exception:
        # Fallback for local development when blob public access is disabled.
        raw_data = ingest_data("data/opsight_sample_sales.csv")

    # Step 2 — Adapter
    canonical_records = adapt_records(raw_data)

    valid_records = []
    invalid_records = []

    # Step 3 — Validation
    for record in canonical_records:

        result = validate_canonical_record(record)

        if result["status"] == "valid":
            valid_records.append(record)
        else:
            invalid_records.append({
                "record": record,
                "errors": result["errors"]
            })

    # Step 4 — Persistence
    config = StorageConfig(backend="json")
    storage = StorageFactory.create_storage(config)

    storage.save_records(valid_records)

    print("Pipeline completed")
    print(f"Valid records: {len(valid_records)}")
    print(f"Invalid records: {len(invalid_records)}")


if __name__ == "__main__":
    run_pipeline()