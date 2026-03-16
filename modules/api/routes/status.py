# modules/api/routes/status.py
import json
from pathlib import Path
from fastapi import APIRouter

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SUMMARY_PATH = PROJECT_ROOT / "reports" / "pipeline_run_summary.json"

@router.get("/pipeline/status")
def get_pipeline_status():
    if not SUMMARY_PATH.exists():
        return {"status": "no runs recorded"}

    with open(SUMMARY_PATH, "r") as f:
        summary = json.load(f)

    return summary