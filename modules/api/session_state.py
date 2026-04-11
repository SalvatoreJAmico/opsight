"""Centralized in-memory session state for API request flows."""

from typing import Any, Dict


PIPELINE_STATUS_ALLOWED = {"not_run", "running", "completed", "failed"}
MODEL_STATUS_ALLOWED = {"idle", "running", "completed"}


def _default_session_state() -> Dict[str, Any]:
    return {
        "active_dataset": None,
        "dataset_source_metadata": None,
        "pipeline_status": "not_run",
        "anomaly_status": "idle",
        "prediction_status": "idle",
        "selected_variables": {"target": None, "compare": []},
    }


_SESSION_STATE = _default_session_state()


def get_session_state() -> Dict[str, Any]:
    return dict(_SESSION_STATE)


def reset_processing_state() -> Dict[str, Any]:
    _SESSION_STATE["pipeline_status"] = "not_run"
    _SESSION_STATE["anomaly_status"] = "idle"
    _SESSION_STATE["prediction_status"] = "idle"
    return get_session_state()


def reset_session_state() -> Dict[str, Any]:
    _SESSION_STATE["active_dataset"] = None
    _SESSION_STATE["dataset_source_metadata"] = None
    _SESSION_STATE["selected_variables"] = {"target": None, "compare": []}
    return reset_processing_state()


def set_active_dataset(dataset_id: str | None) -> Dict[str, Any]:
    if _SESSION_STATE["active_dataset"] != dataset_id:
        _SESSION_STATE["active_dataset"] = dataset_id
        _SESSION_STATE["dataset_source_metadata"] = None
        reset_processing_state()
    return get_session_state()


def set_dataset_source_metadata(source_metadata: Dict[str, Any] | None) -> Dict[str, Any]:
    _SESSION_STATE["dataset_source_metadata"] = dict(source_metadata) if source_metadata else None
    return get_session_state()


def set_pipeline_status(status: str) -> Dict[str, Any]:
    if status not in PIPELINE_STATUS_ALLOWED:
        raise ValueError(f"Invalid pipeline status: {status}")
    _SESSION_STATE["pipeline_status"] = status
    return get_session_state()


def set_anomaly_status(status: str) -> Dict[str, Any]:
    if status not in MODEL_STATUS_ALLOWED:
        raise ValueError(f"Invalid anomaly status: {status}")
    _SESSION_STATE["anomaly_status"] = status
    return get_session_state()


def set_prediction_status(status: str) -> Dict[str, Any]:
    if status not in MODEL_STATUS_ALLOWED:
        raise ValueError(f"Invalid prediction status: {status}")
    _SESSION_STATE["prediction_status"] = status
    return get_session_state()


def set_selected_variables(target: str | None, compare: list) -> Dict[str, Any]:
    _SESSION_STATE["selected_variables"] = {"target": target, "compare": list(compare)}
    return get_session_state()
