# modules/api/routes/status.py
import json
import os
from pathlib import Path
from fastapi import APIRouter
from modules.api.session_state import get_session_state, reset_session_state
from modules.config.storage_config import StorageConfig
from modules.persistence.local_storage import LocalStorage

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[3]
summary_path = os.getenv("PIPELINE_SUMMARY_PATH")
if not summary_path:
    raise RuntimeError("Missing required environment variable: PIPELINE_SUMMARY_PATH")

SUMMARY_PATH = Path(summary_path)

@router.get("/pipeline/status")
def get_pipeline_status():
    if not SUMMARY_PATH.exists():
        return {"status": "no runs recorded"}

    with open(SUMMARY_PATH, "r") as f:
        summary = json.load(f)

    return summary


@router.get("/session/state")
def get_session_state_endpoint():
    return get_session_state()


@router.post("/session/reset")
def reset_session_endpoint():
    config = StorageConfig()
    storage = LocalStorage(storage_path=config.storage_path)
    storage.save_records([])

    state = reset_session_state()
    return {
        "status": "reset",
        "session": state,
    }