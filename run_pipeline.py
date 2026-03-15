"""
Opsight pipeline entrypoint.

Usage:
    python run_pipeline.py <source_path> [backend]

Arguments:
    source_path  Path to the source data file (csv, json, parquet, excel).
    backend      Storage backend to use: "json" (default) or "parquet".

Examples:
    python run_pipeline.py data/opsight_sample_sales.csv
    python run_pipeline.py data/opsight_sample_customers.json parquet
"""

import sys
from modules.pipeline.runner import run_pipeline
from modules.config.storage_config import StorageConfig


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    source_path = sys.argv[1]
    backend = sys.argv[2] if len(sys.argv) > 2 else "json"

    config = StorageConfig(backend=backend)
    summary = run_pipeline(source_path, config)

    print("\n--- Pipeline Summary ---")
    print(f"  Status           : {summary['status']}")
    print(f"  Source           : {summary['source_path']}")
    print(f"  Records Ingested : {summary['records_ingested']}")
    print(f"  Records Adapted  : {summary['records_adapted']}")
    print(f"  Records Valid    : {summary['records_valid']}")
    print(f"  Records Invalid  : {summary['records_invalid']}")
    print(f"  Duplicates Found : {summary['duplicates_found']}")
    print(f"  Records Persisted: {summary['records_persisted']}")
    print(f"  Started At       : {summary.get('started_at', '')}")
    print(f"  Ended At         : {summary.get('ended_at', '')}")

    if summary["errors"]:
        print("\nErrors:")
        for error in summary["errors"]:
            print(f"  - {error}")

    sys.exit(0 if summary["status"] == "success" else 1)


if __name__ == "__main__":
    main()
