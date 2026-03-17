# modules/api/routes/ingest.py
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from run_pipeline import run_pipeline
from modules.api.access_control import require_upload_access_code

router = APIRouter()


def _normalize_source_path(source_path: str) -> str:
    normalized_source_path = source_path
    if isinstance(source_path, str) and not source_path.startswith(("http://", "https://", "sql://")):
        source_file = Path(source_path)
        if not source_file.is_absolute():
            project_root = Path(__file__).resolve().parents[3]
            normalized_source_path = str((project_root / source_file).resolve())
    return normalized_source_path


def _run_pipeline_for_payload(payload: dict):
    source_path = payload.get("source_path")

    if not source_path:
        raise HTTPException(status_code=422, detail="source_path is required")

    normalized_source_path = _normalize_source_path(source_path)

    try:
        summary = run_pipeline(normalized_source_path)

        if summary.get("status") == "FAILED":
            raise HTTPException(status_code=500, detail=f"Pipeline failure at stage: {summary.get('failed_stage')}")

        return {
            "status": "processed",
            "source_path": normalized_source_path,
            "records_ingested": summary.get("records_ingested", 0),
            "records_valid": summary.get("records_valid", 0),
            "records_invalid": summary.get("records_invalid", 0),
            "records_persisted": summary.get("records_persisted", 0),
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline failure: {str(exc)}")


@router.post("/data")
async def ingest_data_endpoint(payload: dict, request: Request):
    await require_upload_access_code(request=request, payload=payload)
    return _run_pipeline_for_payload(payload)


@router.post("/pipeline/trigger")
async def trigger_pipeline_endpoint(payload: dict, request: Request):
    await require_upload_access_code(request=request, payload=payload)
    return _run_pipeline_for_payload(payload)