# modules/api/routes/status.py
import json
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from modules.api.session_state import get_session_state, reset_session_state
from modules.config.storage_config import StorageConfig
from modules.config.runtime_config import load_runtime_config
from modules.persistence.local_storage import LocalStorage

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[3]
summary_path = os.getenv("PIPELINE_SUMMARY_PATH")
if not summary_path:
    raise RuntimeError("Missing required environment variable: PIPELINE_SUMMARY_PATH")

SUMMARY_PATH = Path(summary_path)


def _probe_sql_connection(sql_connection_string: str) -> None:
    try:
        from sqlalchemy import create_engine, text
    except Exception as exc:
        raise RuntimeError("SQLAlchemy is required for SQL startup checks") from exc

    engine = create_engine(sql_connection_string, pool_pre_ping=True)
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

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


@router.post("/sql/start")
def start_sql_server_endpoint():
    runtime_config = load_runtime_config()
    sql_connection_string = runtime_config.sql_connection_string

    if not sql_connection_string:
        raise HTTPException(status_code=400, detail="SQL connection string not configured")

    try:
        _probe_sql_connection(sql_connection_string)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return {
        "status": "ready",
        "message": "SQL Server is ready",
    }