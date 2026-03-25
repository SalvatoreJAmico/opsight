# modules/api/routes/status.py
import json
import os
from pathlib import Path
from fastapi import APIRouter
from modules.api.session_state import get_session_state

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