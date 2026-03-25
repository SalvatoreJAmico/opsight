# modules/api/routes/ingest.py
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from run_pipeline import run_pipeline
from modules.api.access_control import require_upload_access_code
from modules.api.dataset_config import DATASET_MAP
from modules.api.session_state import (
    get_session_state,
    set_active_dataset,
    set_pipeline_status,
)

router = APIRouter()


class PipelineTriggerRequest(BaseModel):
    target: str = "local"
    dataset_id: str


def _normalize_source_path(source_path: str) -> str:
    normalized_source_path = source_path
    if isinstance(source_path, str) and not source_path.startswith(("http://", "https://", "sql://")):
        source_file = Path(source_path)
        if not source_file.is_absolute():
            project_root = Path(__file__).resolve().parents[3]
            resolved_source = (project_root / source_file).resolve()
            # Keep non-existent relative paths unchanged so explicit Blob-style
            # container/blob paths can be routed correctly by ingestion.
            if resolved_source.exists():
                normalized_source_path = str(resolved_source)
    return normalized_source_path


def _run_pipeline_for_payload(payload: dict, use_default_source: bool = False, source_mode: str = None):
    source_path = payload.get("source_path")

    # If use_default_source is True, let ingest_data() choose the default based on env or source_mode
    if use_default_source:
        source_path = None

    if not use_default_source and not source_path:
        raise HTTPException(status_code=422, detail="source_path is required")

    normalized_source_path = _normalize_source_path(source_path) if source_path else None

    try:
        summary = run_pipeline(normalized_source_path, source_mode=source_mode)

        if summary.get("status") == "FAILED":
            failed_stage = summary.get("failed_stage") or "unknown"
            pipeline_error = summary.get("error_message")
            detail = f"Pipeline failure at stage: {failed_stage}"
            if pipeline_error:
                detail = f"{detail}. {pipeline_error}"
            raise HTTPException(status_code=500, detail=detail)

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
async def trigger_pipeline_endpoint(payload: PipelineTriggerRequest, request: Request):
    # Phase 14: /pipeline/trigger no longer requires access code.
    # Frontend sends { "target": "local" | "cloud" }; backend respects this choice.
    payload_dict = payload.model_dump()
    target = payload_dict.get("target", "local")
    if target not in ("local", "cloud"):
        raise HTTPException(status_code=400, detail="target must be 'local' or 'cloud'")

    dataset = DATASET_MAP.get(payload.dataset_id)
    if not dataset:
        raise HTTPException(status_code=400, detail="Unknown dataset_id")

    current_state = get_session_state()
    if current_state["active_dataset"] != payload.dataset_id:
        set_active_dataset(payload.dataset_id)

    source_type = dataset.get("source_type")

    if source_type == "blob":
        selected_source = {
            "source_type": "blob",
            "format": dataset.get("format"),
            "path": dataset.get("path"),
        }
        if not selected_source["path"]:
            raise HTTPException(status_code=400, detail="Dataset path is not configured")

        set_pipeline_status("running")
        try:
            response = _run_pipeline_for_payload(
                {"source_path": selected_source["path"]},
                use_default_source=False,
                source_mode=target,
            )
            set_pipeline_status("completed")
        except Exception:
            set_pipeline_status("failed")
            raise
        response["dataset_id"] = payload.dataset_id
        response["dataset_source_type"] = selected_source["source_type"]
        response["dataset_path"] = selected_source["path"]
        return response

    if source_type == "sql":
        selected_source = {
            "source_type": "sql",
            "database": dataset.get("database"),
            "schema": dataset.get("schema"),
            "table": dataset.get("table"),
        }
        if not selected_source["schema"] or not selected_source["table"]:
            raise HTTPException(status_code=400, detail="SQL dataset is not configured correctly")
        raise HTTPException(status_code=501, detail="SQL dataset execution not wired yet")

    raise HTTPException(status_code=400, detail="Unsupported dataset source_type")