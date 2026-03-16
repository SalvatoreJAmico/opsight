# modules/api/routes/ingest.py
from fastapi import APIRouter, HTTPException
from modules.ingestion.ingestion import ingest_data
from modules.adapter.adapter import adapt_records
from modules.validation.validator import validate_canonical_record
from modules.persistence.storage_factory import StorageFactory
from configs.storage_config import StorageConfig

router = APIRouter()

@router.post("/data")
def ingest_data_endpoint(payload: dict):
    source_path = payload.get("source_path")

    if not source_path:
        raise HTTPException(status_code=422, detail="source_path is required")

    try:
        raw_data = ingest_data(source_path)
        canonical_records = adapt_records(raw_data)

        valid_records = []
        invalid_records = []

        for record in canonical_records:
            result = validate_canonical_record(record)
            if result["status"] == "valid":
                valid_records.append(record)
            else:
                invalid_records.append(record)

        storage_config = StorageConfig(backend="json")
        storage = StorageFactory.create_storage(storage_config)
        storage.save_records(valid_records)

        return {
            "status": "processed",
            "source_path": source_path,
            "records_ingested": len(raw_data),
            "records_valid": len(valid_records),
            "records_invalid": len(invalid_records),
            "records_persisted": len(valid_records),
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline failure: {str(exc)}")