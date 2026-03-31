# modules/api/routes/status.py
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Literal
from fastapi import APIRouter
from pydantic import BaseModel
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
DEFAULT_SQL_DOCKER_SERVICE = "opsight-sqlserver"
SQL_STARTUP_TIMEOUT_SECONDS = 60
SQL_STARTUP_POLL_INTERVAL_SECONDS = 2


class SqlStartRequest(BaseModel):
    target: Literal["local", "cloud"] = "local"


def _probe_sql_connection(sql_connection_string: str) -> None:
    try:
        from sqlalchemy import create_engine, text
    except Exception as exc:
        raise RuntimeError("SQLAlchemy is required for SQL startup checks") from exc

    engine = create_engine(
        sql_connection_string,
        pool_pre_ping=True,
        connect_args={"timeout": 10},
    )
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def _format_sql_start_error(exc: Exception) -> str:
    error_text = str(exc)
    lowered_error_text = error_text.lower()

    if "hyt00" in lowered_error_text or "login timeout expired" in lowered_error_text:
        return (
            "Could not connect to SQL Server (connection timed out). "
            "Verify SQL_CONNECTION_STRING server, port, credentials, and firewall access."
        )

    if "[28000]" in error_text or "login failed" in lowered_error_text:
        return "Could not connect to SQL Server (login failed). Check SQL username and password."

    if "data source name not found" in lowered_error_text or "odbc driver" in lowered_error_text:
        return "Could not connect to SQL Server (ODBC driver issue). Confirm ODBC Driver 18 for SQL Server is installed."

    return f"Could not connect to SQL Server. {error_text}"


def _run_sql_start_command() -> tuple[bool, str]:
    configured_start_command = os.getenv("SQL_START_COMMAND")
    if configured_start_command:
        try:
            process_result = subprocess.run(
                configured_start_command,
                cwd=str(PROJECT_ROOT),
                shell=True,
                capture_output=True,
                text=True,
                timeout=90,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return False, "SQL start command timed out"
        except Exception as exc:
            return False, f"SQL start command failed to execute: {exc}"

        if process_result.returncode != 0:
            stderr = (process_result.stderr or "").strip()
            stdout = (process_result.stdout or "").strip()
            details = stderr or stdout or "unknown startup error"
            return False, f"SQL start command failed: {details}"

        return True, "SQL start command completed"

    sql_docker_service = os.getenv("SQL_DOCKER_SERVICE", DEFAULT_SQL_DOCKER_SERVICE)

    try:
        docker_version_result = subprocess.run(
            ["docker", "compose", "version"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except FileNotFoundError:
        return False, (
            "No SQL startup method is configured. Set SQL_START_COMMAND or install Docker Desktop "
            "and add an opsight-sqlserver service in docker-compose.yml"
        )
    except Exception as exc:
        return False, f"Could not run docker compose: {exc}"

    if docker_version_result.returncode != 0:
        stderr = (docker_version_result.stderr or "").strip()
        lowered_stderr = stderr.lower()
        if "dockerdesktoplinuxengine" in lowered_stderr or "daemon" in lowered_stderr:
            return False, "Docker Desktop is installed but not running. Start Docker Desktop, then try again."
        return False, f"Docker compose is not available: {stderr or 'unknown error'}"

    try:
        docker_up_result = subprocess.run(
            ["docker", "compose", "up", "-d", sql_docker_service],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False, "Timed out while starting SQL Server container"
    except Exception as exc:
        return False, f"Could not start SQL Server container: {exc}"

    if docker_up_result.returncode != 0:
        stderr = (docker_up_result.stderr or "").strip()
        stdout = (docker_up_result.stdout or "").strip()
        details = stderr or stdout or "unknown docker startup error"
        lowered_details = details.lower()
        if "dockerdesktoplinuxengine" in lowered_details or "daemon" in lowered_details:
            return False, "Docker Desktop is installed but not running. Start Docker Desktop, then try again."
        return False, f"Could not start SQL Server container: {details}"

    return True, f"SQL Server container startup requested for service '{sql_docker_service}'"


def _wait_for_sql_ready(sql_connection_string: str) -> Exception | None:
    deadline = time.time() + SQL_STARTUP_TIMEOUT_SECONDS
    last_exception = None

    while time.time() < deadline:
        try:
            _probe_sql_connection(sql_connection_string)
            return None
        except Exception as exc:
            last_exception = exc
            time.sleep(SQL_STARTUP_POLL_INTERVAL_SECONDS)

    return last_exception

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
def start_sql_server_endpoint(payload: SqlStartRequest):
    runtime_config = load_runtime_config()
    sql_connection_string = runtime_config.sql_connection_string
    target = payload.target

    if not sql_connection_string:
        return {
            "status": "not_ready",
            "ready": False,
            "message": "SQL connection string not configured",
        }

    try:
        _probe_sql_connection(sql_connection_string)
    except Exception as initial_exception:
        if target == "cloud":
            return {
                "status": "not_ready",
                "ready": False,
                "message": (
                    "Cloud mode can only validate SQL connectivity and cannot start a SQL Server process. "
                    f"{_format_sql_start_error(initial_exception)}"
                ),
            }

        started, startup_message = _run_sql_start_command()
        if not started:
            return {
                "status": "not_ready",
                "ready": False,
                "message": (
                    f"{_format_sql_start_error(initial_exception)} "
                    f"{startup_message}"
                ),
            }

        final_exception = _wait_for_sql_ready(sql_connection_string)
        if final_exception is not None:
            return {
                "status": "not_ready",
                "ready": False,
                "message": (
                    "SQL Server startup was triggered but the instance is still unreachable. "
                    f"{_format_sql_start_error(final_exception)}"
                ),
            }

        return {
            "status": "ready",
            "ready": True,
            "message": "SQL Server started and is ready",
            "startup": startup_message,
        }

    return {
        "status": "ready",
        "ready": True,
        "message": "SQL Server is ready",
    }